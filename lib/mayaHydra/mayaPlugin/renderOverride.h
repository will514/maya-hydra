//
// Copyright 2019 Luma Pictures
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Copyright 2023 Autodesk
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
#ifndef MTOH_VIEW_OVERRIDE_H
#define MTOH_VIEW_OVERRIDE_H

#include "renderGlobals.h"
#include "pluginUtils.h"

#include <mayaHydraLib/delegates/delegate.h>
#include <mayaHydraLib/delegates/params.h>
#include <mayaHydraLib/mayaHydraSceneProducer.h>
#include <mayaHydraLib/sceneIndex/mayaHydraSceneIndexDataFactoriesSetup.h>

#include <flowViewport/sceneIndex/fvpRenderIndexProxyFwd.h>
#include <flowViewport/sceneIndex/fvpSelectionSceneIndex.h>
#include <flowViewport/selection/fvpSelectionTracker.h>
#include <flowViewport/selection/fvpSelectionFwd.h>

#include <pxr/base/tf/singleton.h>
#include <pxr/imaging/hd/driver.h>
#include <pxr/imaging/hd/engine.h>
#include <pxr/imaging/hd/renderIndex.h>
#include <pxr/imaging/hd/rendererPlugin.h>
#include <pxr/imaging/hd/rprimCollection.h>
#include <pxr/imaging/hd/pluginRenderDelegateUniqueHandle.h>
#include <pxr/imaging/hdSt/renderDelegate.h>
#include <pxr/imaging/hdx/taskController.h>
#include <pxr/pxr.h>

#include <maya/MCallbackIdArray.h>
#include <maya/MMessage.h>
#include <maya/MObjectHandle.h>
#include <maya/MString.h>
#include <maya/MViewport2Renderer.h>

#include <atomic>
#include <chrono>
#include <memory>
#include <mutex>

#include <ufe/ufe.h>
UFE_NS_DEF {
class SelectionChanged;
}

PXR_NAMESPACE_OPEN_SCOPE
// Remove this using statement once the following code is moved into the MayaHydra namespace
using MtohRendererDescription = MayaHydra::MtohRendererDescription;

using HgiUniquePtr = std::unique_ptr<class Hgi>;
class MayaHydraSceneIndexRegistry;
class MayaHydraSceneDelegate;
using HdxPickHitVector = std::vector<struct HdxPickHit>;

/*! \brief MtohRenderOverride is a rendering override class for the viewport to use Hydra instead of
 * VP2.0.
 */
class MtohRenderOverride : public MHWRender::MRenderOverride
{
public:
    MtohRenderOverride(const MtohRendererDescription& desc);
    ~MtohRenderOverride() override;

    /// Mark a setting (or all settings when attrName is '') as out of date
    static void UpdateRenderGlobals(const MtohRenderGlobals& globals, const TfToken& attrName = {});

    /// The names of all render delegates that are being used by at least
    /// one modelEditor panel.
    static std::vector<MString> AllActiveRendererNames();

    /// Returns a list of rprims in the render index for the given render
    /// delegate.
    ///
    /// Intended mostly for use in debugging and testing.
    static SdfPathVector RendererRprims(TfToken rendererName, bool visibleOnly = false);

    /// Returns the scene delegate id for the given render delegate and
    /// scene delegate names.
    ///
    /// Intended mostly for use in debugging and testing.
    static SdfPath RendererSceneDelegateId(TfToken rendererName, TfToken sceneDelegateName);

    //! Main entry point for rendering, called by Maya.
    MStatus Render(
        const MHWRender::MDrawContext&                         drawContext,
        const MHWRender::MDataServerOperation::MViewportScene& scene);

    void ClearHydraResources();
    void SelectionChanged(const Ufe::SelectionChanged& notification);
    void SetRenderPurposeTags(const MayaHydraParams& delegateParams) { _SetRenderPurposeTags(delegateParams); };
    MString uiName() const override { return MString(_rendererDesc.displayName.GetText()); }

    MHWRender::DrawAPI supportedDrawAPIs() const override;

    MStatus setup(const MString& destination) override;
    MStatus cleanup() override;

    bool                         startOperationIterator() override;
    MHWRender::MRenderOperation* renderOperation() override;
    bool                         nextRenderOperation() override;

    bool select(
        const MHWRender::MFrameContext&  frameContext,
        const MHWRender::MSelectionInfo& selectInfo,
        bool                             useDepth,
        MSelectionList&                  selectionList,
        MPointArray&                     worldSpaceHitPts) override;

private:
    typedef std::pair<MString, MCallbackIdArray> PanelCallbacks;
    typedef std::vector<PanelCallbacks>          PanelCallbacksList;

    static MtohRenderOverride* _GetByName(TfToken rendererName);

    void              _InitHydraResources(const MHWRender::MDrawContext& drawContext);
    void              _RemovePanel(MString panelName);
    void              _DetectMayaDefaultLighting(const MHWRender::MDrawContext& drawContext);
    HdRenderDelegate* _GetRenderDelegate();
    void              _SetRenderPurposeTags(const MayaHydraParams& delegateParams);
    void              _CreateSceneIndicesChainAfterMergingSceneIndex();

    void _PickByRegion(
        HdxPickHitVector& outHits,
        const MMatrix& viewMatrix,
        const MMatrix& projMatrix,
        bool pointSnappingActive,
        int view_x,
        int view_y,
        int view_w,
        int view_h,
        unsigned int sel_x,
        unsigned int sel_y,
        unsigned int sel_w,
        unsigned int sel_h);

    inline PanelCallbacksList::iterator _FindPanelCallbacks(MString panelName)
    {
        // There should never be that many render panels, so linear iteration
        // should be fine

        return std::find_if(
            _renderPanelCallbacks.begin(),
            _renderPanelCallbacks.end(),
            [&panelName](const PanelCallbacks& item) { return item.first == panelName; });
    }

    MAYAHYDRALIB_API
    void _PopulateSelectionList(
        const HdxPickHitVector&          hits,
        const MHWRender::MSelectionInfo& selectInfo,
        MSelectionList&                  selectionList,
        MPointArray&                     worldSpaceHitPts);

    void _AddPluginSelectionHighlighting();

    // Callbacks
    static void _ClearHydraCallback(void* data);
    static void _TimerCallback(float, float, void* data);
    static void _PlayblastingChanged(bool state, void*);
    static void _PanelDeletedCallback(const MString& panelName, void* data);
    static void _RendererChangedCallback(
        const MString& panelName,
        const MString& oldRenderer,
        const MString& newRenderer,
        void*          data);
    static void _RenderOverrideChangedCallback(
        const MString& panelName,
        const MString& oldOverride,
        const MString& newOverride,
        void*          data);

    MtohRendererDescription _rendererDesc;

    std::shared_ptr<MayaHydraSceneIndexRegistry> _sceneIndexRegistry;
    std::vector<MHWRender::MRenderOperation*>    _operations;
    MCallbackIdArray                             _callbacks;
    MCallbackId                                  _timerCallback = 0;
    PanelCallbacksList                           _renderPanelCallbacks;
    const MtohRenderGlobals&                     _globals;

    std::mutex                            _lastRenderTimeMutex;
    std::chrono::system_clock::time_point _lastRenderTime;
    std::atomic<bool>                     _backupFrameBufferWorkaround = { false };
    std::atomic<bool>                     _playBlasting = { false };
    std::atomic<bool>                     _isConverged = { false };
    std::atomic<bool>                     _needsClear = { false };

    /// Hgi and HdDriver should be constructed before HdEngine to ensure they
    /// are destructed last. Hgi may be used during engine/delegate destruction.
    HgiUniquePtr                              _hgi;
    HdDriver                                  _hgiDriver;
    HdEngine                                  _engine;
    HdRendererPlugin*                         _rendererPlugin = nullptr;
    HdxTaskController*                        _taskController = nullptr;
    HdPluginRenderDelegateUniqueHandle        _renderDelegate = nullptr;
    Fvp::RenderIndexProxyPtr                  _renderIndexProxy{nullptr};
    HdRenderIndex*                            _renderIndex = nullptr;
    Fvp::SelectionTrackerSharedPtr            _fvpSelectionTracker;
    Fvp::SelectionSceneIndexRefPtr            _selectionSceneIndex;
    Fvp::SelectionPtr                         _selection;
    class SelectionObserver;
    using SelectionObserverPtr = std::shared_ptr<SelectionObserver>;
    SelectionObserverPtr                      _mayaSelectionObserver;
    HdRprimCollection                         _renderCollection { HdTokens->geometry,
                                          HdReprSelector(HdReprTokens->refined),
                                          SdfPath::AbsoluteRootPath() };

    HdRprimCollection _pointSnappingCollection {
        HdTokens->geometry,
        HdReprSelector(HdReprTokens->refined, TfToken(), HdReprTokens->points),
        SdfPath::AbsoluteRootPath()
    };

    GlfSimpleLight _defaultLight;

    std::unique_ptr<MayaHydraSceneProducer> _mayaHydraSceneProducer;

    /** This class creates the scene index data factories and set them up into the flow viewport library to be able to create DCC 
    *   specific scene index data classes without knowing their content in Flow viewport.
    *   This is done in the constructor of this class
    */
    MAYAHYDRA_NS_DEF::SceneIndexDataFactoriesSetup  _sceneIndexDataFactoriesSetup;

    SdfPath _ID;

    GfVec4d _viewport;

    int _currentOperation = -1;

    const bool _isUsingHdSt = false;
    bool       _initializationAttempted = false;
    bool       _initializationSucceeded = false;
    bool       _hasDefaultLighting = false;
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif // MTOH_VIEW_OVERRIDE_H
