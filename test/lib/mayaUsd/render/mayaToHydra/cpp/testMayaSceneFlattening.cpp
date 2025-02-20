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

#include "testUtils.h"

#include <mayaHydraLib/hydraUtils.h>
#include <mayaHydraLib/mayaUtils.h>

#include <pxr/imaging/hd/tokens.h>

#include <maya/MViewport2Renderer.h>

#include <gtest/gtest.h>

PXR_NAMESPACE_USING_DIRECTIVE

using namespace MayaHydra;

TEST(MayaSceneFlattening, childHasFlattenedTransform)
{
    // Setup inspector for the first scene index
    const SceneIndicesVector& sceneIndices = GetTerminalSceneIndices();
    ASSERT_GT(sceneIndices.size(), static_cast<size_t>(0));
    SceneIndexInspector inspector(sceneIndices.front());

    // Retrieve the child cube prim
    FindPrimPredicate findCubePrimPredicate
        = [](const HdSceneIndexBasePtr& sceneIndex, const SdfPath& primPath) -> bool {
        HdSceneIndexPrim prim = sceneIndex->GetPrim(primPath);
        if (prim.primType != HdPrimTypeTokens->mesh) {
            return false;
        }
        bool parentIsCube
            = MakeRelativeToParentPath(primPath.GetParentPath()).GetAsString() == "childCubeShape";
        return parentIsCube;
    };
    PrimEntriesVector foundPrims = inspector.FindPrims(findCubePrimPredicate, 1);
    ASSERT_EQ(foundPrims.size(), static_cast<size_t>(1));
    HdSceneIndexPrim cubePrim = foundPrims.front().prim;

    // Extract the Hydra xform matrix from the cube prim
    GfMatrix4d cubeHydraMatrix;
    ASSERT_TRUE(GetXformMatrixFromPrim(cubePrim, cubeHydraMatrix));

    // Retrieve the child cube Maya DAG path
    MDagPath cubeDagPath;
    ASSERT_TRUE(GetDagPathFromNodeName("childCube", cubeDagPath));

    // Extract the Maya matrix from the cube DAG path
    MMatrix cubeMayaMatrix;
    ASSERT_TRUE(GetMayaMatrixFromDagPath(cubeDagPath, cubeMayaMatrix));

    // Make sure that both the Hydra and Maya flattened transforms match
    EXPECT_TRUE(MatricesAreClose(cubeHydraMatrix, cubeMayaMatrix))
        << "Hydra matrix " << cubeHydraMatrix << " was not close enough to Maya Matrix "
        << cubeMayaMatrix;
}
