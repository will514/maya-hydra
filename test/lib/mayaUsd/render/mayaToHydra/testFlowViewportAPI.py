#
# Copyright 2023 Autodesk, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from math import*
import maya.cmds as cmds
import maya.api.OpenMaya as om
import fixturesUtils
import mtohUtils
import maya.mel as mel
from testUtils import PluginLoaded

def setRotateY(matrixAsAList, angle):
    ''' Sets the matrix as a list of values to be a Rotate about Y matrix (deg), and returns it'''
    angle *=  (pi/180);
    matrixAsAList[0] = cos(angle)
    matrixAsAList[2+4*2] = cos(angle)
    matrixAsAList[0+4*2] = -sin(angle)
    matrixAsAList[2+4*0] = sin(angle)
    return matrixAsAList

class TestFlowViewportAPI(mtohUtils.MtohTestCase): #Subclassing mtohUtils.MtohTestCase to be able to call self.assertSnapshotClose
    # MayaHydraBaseTestCase.setUpClass requirement.
    _file = __file__

    def setupScene(self):
        self.setHdStormRenderer()

    #Test adding primitives
    def test_AddingPrimitives(self):
        self.setupScene()
        with PluginLoaded('flowViewportAPIMayaLocator'):
            
            #Create a maya sphere
            sphereNode, sphereShape = cmds.polySphere()
            cmds.refresh()

            #Create a FlowViewportAPIMayaLocator node which adds a dataProducerSceneIndex and a Filtering scene index
            flowViewportNodeName = cmds.createNode("FlowViewportAPIMayaLocator")
            self.assertFalse(flowViewportNodeName == None)
            #When the node above is created, its compute method is not called automatically, so work around to trigger a call to compute
            cmds.setAttr(flowViewportNodeName + '.dummyInput', 2)#setting this will set dirty the dummyOutput attribute
            cmds.getAttr(flowViewportNodeName + '.dummyOutput')#getting this value will trigger a call to compute
            cmds.refresh()
            #Original images are located for example in maya-hydra\test\lib\mayaUsd\render\mayaToHydra\FlowViewportAPITest
            self.assertSnapshotClose("add_NodeCreated.png", None, None)

            #Move the transform node, the added prims (cube grid) should move as well
            # Get the transform node of the FlowViewportAPIMayaLocator
            transformNode = cmds.listRelatives(flowViewportNodeName, parent=True)[0]
            self.assertFalse(transformNode == None)
            #Select the transform node
            cmds.select(transformNode)
            # Move the selected node
            cmds.move(10, 5, -5)
            cmds.refresh()
            self.assertSnapshotClose("add_NodeMoved.png", None, None)
        
            #Hide the transform node, this should hide the FlowViewportAPIMayaLocator node and the added prims as well.
            cmds.hide(transformNode)
            self.assertSnapshotClose("add_NodeHidden.png", None, None)

            #Unhide the transform node, this should unhide the FlowViewportAPIMayaLocator node and the added prims as well.
            cmds.showHidden(transformNode)
            self.assertSnapshotClose("add_NodeUnhidden.png", None, None)

            #Delete the shape node
            cmds.delete(flowViewportNodeName)
            
            self.assertSnapshotClose("add_NodeDeleted.png", None, None)
            #Enable undo again
            cmds.undoInfo(stateWithoutFlush=True)

            #Undo the delete, the node should be visible again
            cmds.undo()
            self.assertSnapshotClose("add_NodeDeletedUndo.png", None, None)

            #Redo the delete
            cmds.redo()
            self.assertSnapshotClose("add_NodeDeletedRedo.png", None, None)

            #Undo the delete again, the node should be visible again
            cmds.undo()
            self.assertSnapshotClose("add_NodeDeletedUndoAgain.png", None, None)

            #Move transform node again to see if it still updates the added prims transform
            cmds.select(transformNode)
            # Move the selected node
            cmds.move(-20, -5, 0)
            cmds.refresh()
            self.assertSnapshotClose("add_NodeMovedAfterDeletionAndUndo.png", None, None)

            #Switch to VP2
            self.setViewport2Renderer()
            #Switch back to Storm
            self.setHdStormRenderer()
            self.assertSnapshotClose("add_VP2AndThenBackToStorm.png", None, None)

            #Finish by a File New command
            cmds.file(new=True, force=True)

    #Test Cube grids parameters
    def test_CubeGrid(self):
        self.setupScene()
        with PluginLoaded('flowViewportAPIMayaLocator'):
            
            #Create a FlowViewportAPIMayaLocator node which adds a dataProducerSceneIndex and a Filtering scene index
            flowViewportNodeName = cmds.createNode("FlowViewportAPIMayaLocator")
            self.assertFalse(flowViewportNodeName == None)

            #When the node above is created, its compute method is not called automatically, so work around to trigger a call to compute
            cmds.setAttr(flowViewportNodeName + '.dummyInput', 2)#setting this will set dirty the dummyOutput attribute
            cmds.getAttr(flowViewportNodeName + '.dummyOutput')#getting this value will trigger a call to compute
            self.assertSnapshotClose("cubeGrid_BeforeModifs.png", None, None)

            #Get the matrix and set a rotation of 70 degress around Y axis.
            matrix = cmds.getAttr(flowViewportNodeName + '.cubeInitalTransform')
            #Set it to have its rotation be a rotation around Y of 70 deg.
            setRotateY(matrix, 70)

            #Modify the cube grid parameters
            cmds.setAttr(flowViewportNodeName + '.numCubesX', 3)
            cmds.setAttr(flowViewportNodeName + '.numCubesY', 2)
            cmds.setAttr(flowViewportNodeName + '.numCubesZ', 3)
            cmds.setAttr(flowViewportNodeName + '.cubeHalfSize', 0.5)
            cmds.setAttr(flowViewportNodeName + '.cubeInitalTransform', matrix, type="matrix")
            cmds.setAttr(flowViewportNodeName + '.cubeColor', 1.0, 1.0, 0.0, type="double3")
            cmds.setAttr(flowViewportNodeName + '.cubeOpacity', 0.2)
            cmds.setAttr(flowViewportNodeName + '.cubesUseInstancing', False)
            cmds.setAttr(flowViewportNodeName + '.cubesDeltaTrans', 15, 15, 15, type="double3")
            cmds.refresh()
            self.assertSnapshotClose("cubeGrid_AfterModifs.png", None, None)

            #Test instancing
            cmds.setAttr(flowViewportNodeName + '.cubesUseInstancing', True)
            cmds.refresh()
            self.assertSnapshotClose("cubeGrid_WithInstancing.png", None, None)

            #Add more cubes
            cmds.setAttr(flowViewportNodeName + '.numCubesX', 30)
            cmds.setAttr(flowViewportNodeName + '.numCubesY', 30)
            cmds.setAttr(flowViewportNodeName + '.numCubesZ', 30)
            cmds.setAttr(flowViewportNodeName + '.cubeColor', 0.0, 0.5, 1.0, type="double3")
            cmds.setAttr(flowViewportNodeName + '.cubeOpacity', 0.3)
            cmds.setAttr(flowViewportNodeName + '.cubesDeltaTrans', 5, 5, 5, type="double3")
            cmds.refresh()
            self.assertSnapshotClose("cubeGrid_WithInstancingModifs.png", None, None)

            #Switch to VP2
            self.setViewport2Renderer()
            #Switch back to Storm
            self.setHdStormRenderer()
            self.assertSnapshotClose("cubeGrid_VP2AndThenBackToStorm.png", None, None)

            #Finish by a File New command
            cmds.file(new=True, force=True)

    #Test multiple nodes
    def test_MultipleNodes(self):
        self.setupScene()
        with PluginLoaded('flowViewportAPIMayaLocator'):
            
            #Create a FlowViewportAPIMayaLocator node which adds a dataProducerSceneIndex and a Filtering scene index
            flowViewportNodeName1 = cmds.createNode("FlowViewportAPIMayaLocator", n="nodeShape1")
            self.assertFalse(flowViewportNodeName1 == None)

            #When the node above is created, its compute method is not called automatically, so work around to trigger a call to compute
            cmds.setAttr(flowViewportNodeName1 + '.dummyInput', 2)#setting this will set dirty the dummyOutput attribute
            cmds.getAttr(flowViewportNodeName1 + '.dummyOutput')#getting this value will trigger a call to compute
            
            #Get the matrix and set a rotation of 70 degress around Y axis.
            matrix = cmds.getAttr(flowViewportNodeName1 + '.cubeInitalTransform')
            #Set it to have its rotation be a rotation around Y of 70 deg.
            setRotateY(matrix, 70)

            #Modify the cube grid parameters
            cmds.setAttr(flowViewportNodeName1 + '.numCubesX', 3)
            cmds.setAttr(flowViewportNodeName1 + '.numCubesY', 3)
            cmds.setAttr(flowViewportNodeName1 + '.numCubesZ', 3)
            cmds.setAttr(flowViewportNodeName1 + '.cubeHalfSize', 0.5)
            cmds.setAttr(flowViewportNodeName1 + '.cubeInitalTransform', matrix, type="matrix")
            cmds.setAttr(flowViewportNodeName1 + '.cubeColor', 1.0, 0.0, 0.0, type="double3")
            cmds.setAttr(flowViewportNodeName1 + '.cubeOpacity', 0.2)
            cmds.setAttr(flowViewportNodeName1 + '.cubesUseInstancing', False)
            cmds.setAttr(flowViewportNodeName1 + '.cubesDeltaTrans', 5, 5, 5, type="double3")
            cmds.refresh()
            
            #Move the transform node, the added prims (cube grid) should move as well
            # Get the transform node of the FlowViewportAPIMayaLocator
            transformNode1 = cmds.listRelatives(flowViewportNodeName1, parent=True)[0]
            self.assertFalse(transformNode1 == None)
            #Select the transform node
            cmds.select(transformNode1)
            # Move the selected node
            cmds.move(-10, 0, 0)
            cmds.refresh()
            
            #Create a FlowViewportAPIMayaLocator node which adds a dataProducerSceneIndex and a Filtering scene index
            flowViewportNodeName2 = cmds.createNode("FlowViewportAPIMayaLocator", n="nodeShape2")
            self.assertFalse(flowViewportNodeName2 == None)

            #When the node above is created, its compute method is not called automatically, so work around to trigger a call to compute
            cmds.setAttr(flowViewportNodeName2 + '.dummyInput', 3)#setting this will set dirty the dummyOutput attribute
            cmds.getAttr(flowViewportNodeName2 + '.dummyOutput')#getting this value will trigger a call to compute
            
            #Get the matrix and set a rotation of 70 degress around Y axis.
            matrix = cmds.getAttr(flowViewportNodeName2 + '.cubeInitalTransform')
            #Set it to have its rotation be a rotation around Y of 70 deg.
            setRotateY(matrix, 20)

            #Modify the cube grid parameters
            cmds.setAttr(flowViewportNodeName2 + '.cubesUseInstancing', True) #Setting instancing to true first make it go faster when changing the number of cubes
            cmds.setAttr(flowViewportNodeName2 + '.numCubesX', 10)
            cmds.setAttr(flowViewportNodeName2 + '.numCubesY', 10)
            cmds.setAttr(flowViewportNodeName2 + '.numCubesZ', 1)
            cmds.setAttr(flowViewportNodeName2 + '.cubeHalfSize', 2)
            cmds.setAttr(flowViewportNodeName2 + '.cubeInitalTransform', matrix, type="matrix")
            cmds.setAttr(flowViewportNodeName2 + '.cubeColor', 0.0, 0.0, 1.0, type="double3")
            cmds.setAttr(flowViewportNodeName2 + '.cubeOpacity', 0.8)
            cmds.setAttr(flowViewportNodeName2 + '.cubesDeltaTrans', 10, 10, 10, type="double3")
            cmds.refresh()
            
            #Move the transform node, the added prims (cube grid) should move as well
            # Get the transform node of the FlowViewportAPIMayaLocator
            transformNode2 = cmds.listRelatives(flowViewportNodeName2, parent=True)[0]
            self.assertFalse(transformNode2 == None)
            #Select the transform node
            cmds.select(transformNode2)
            # Move the selected node
            cmds.move(-30, 0, -30)
            cmds.refresh()
            
            self.assertSnapshotClose("multipleNodes_BeforeModifs.png", None, None)

            #Modify the color of node #2, it shouldn't change node's #1 color
            cmds.setAttr(flowViewportNodeName2 + '.cubeColor', 1.0, 1.0, 1.0, type="double3")
            cmds.setAttr(flowViewportNodeName2 + '.cubeOpacity', 0.1)

            # Apply transform on node #2
            cmds.select(transformNode2)
            cmds.move(-30, 0, 0)
            cmds.rotate(-30, 45, 0)
            cmds.scale(2, 1, 1)
            cmds.refresh()
            self.assertSnapshotClose("multipleNodes_AfterModifs.png", None, None)

            #Remove instancing, the cubes should stay at the same place
            cmds.setAttr(flowViewportNodeName2 + '.cubesUseInstancing', False)
            self.assertSnapshotClose("multipleNodes_AfterModifsRemoveInstancing.png", None, None)

            #Hide node #1
            cmds.hide(transformNode1)
            self.assertSnapshotClose("multipleNodes_Node1Hidden.png", None, None)

            #Unhide node #1
            cmds.showHidden(transformNode1)
            self.assertSnapshotClose("multipleNodes_Node1Unhidden.png", None, None)

            #Switch to VP2
            self.setViewport2Renderer()
            #Switch back to Storm
            self.setHdStormRenderer()
            self.assertSnapshotClose("multipleNodes_VP2AndThenBackToStorm.png", None, None)

            #Finish by a File New command
            cmds.file(new=True, force=True)

    #Test multiple viewports
    def test_MultipleViewports(self):
        with PluginLoaded('flowViewportAPIMayaLocator'):
            #switch to 4 views
            mel.eval('FourViewLayout')
            #Set focus on persp view
            cmds.setFocus ('modelPanel4') #Is the persp view
            #Set Storm as the renderer
            self.setHdStormRenderer()
            
            #Set focus on model Panel 2 (it's an orthographic view : right) 
            cmds.setFocus ('modelPanel2')
            #Set Storm as the renderer
            self.setHdStormRenderer()
            
            #Create a maya sphere
            sphereNode, sphereShape = cmds.polySphere()
            #Select the transform node
            cmds.select(sphereNode)
            # Move the selected node
            cmds.move(15, 0, 0)
            cmds.refresh()

            #Create a FlowViewportAPIMayaLocator node which adds a dataProducerSceneIndex and a Filtering scene index
            flowViewportNodeName1 = cmds.createNode("FlowViewportAPIMayaLocator", n="nodeShape1")
            self.assertFalse(flowViewportNodeName1 == None)

            #When the node above is created, its compute method is not called automatically, so work around to trigger a call to compute
            cmds.setAttr(flowViewportNodeName1 + '.dummyInput', 2)#setting this will set dirty the dummyOutput attribute
            cmds.getAttr(flowViewportNodeName1 + '.dummyOutput')#getting this value will trigger a call to compute
            
            #Modify the cube grid parameters
            cmds.setAttr(flowViewportNodeName1 + '.numCubesX', 3)
            cmds.setAttr(flowViewportNodeName1 + '.numCubesY', 3)
            cmds.setAttr(flowViewportNodeName1 + '.numCubesZ', 3)
            cmds.setAttr(flowViewportNodeName1 + '.cubeHalfSize', 1.0)
            cmds.setAttr(flowViewportNodeName1 + '.cubeColor', 1.0, 0.0, 0.0, type="double3")
            cmds.setAttr(flowViewportNodeName1 + '.cubeOpacity', 0.8)
            cmds.setAttr(flowViewportNodeName1 + '.cubesUseInstancing', False)
            cmds.setAttr(flowViewportNodeName1 + '.cubesDeltaTrans', 3, 3, 3, type="double3")
            cmds.refresh()
            
            cmds.setFocus ('modelPanel4')
            self.assertSnapshotClose("multipleViewports_viewPanel4.png", None, None)
            cmds.setFocus ('modelPanel2')
            self.assertSnapshotClose("multipleViewports_viewPanel2.png", None, None)

            #Switch to VP2
            cmds.setFocus ('modelPanel4')
            self.setViewport2Renderer()
            self.assertSnapshotClose("multipleViewports_VP2_modPan4.png", None, None)
            cmds.setFocus ('modelPanel2')
            self.setViewport2Renderer()
            self.assertSnapshotClose("multipleViewports_VP2_modPan2.png", None, None)
            
            #Switch back to Storm
            cmds.setFocus ('modelPanel4')
            self.setHdStormRenderer()
            self.assertSnapshotClose("multipleViewports_VP2AndThenBackToStorm_modPan4.png", None, None)
            cmds.setFocus ('modelPanel2')
            self.setHdStormRenderer()
            self.assertSnapshotClose("multipleViewports_VP2AndThenBackToStorm_modPan2.png", None, None)

            #Finish by a File New command
            cmds.file(new=True, force=True)
if __name__ == '__main__':
    fixturesUtils.runTests(globals())
