import random
from itertools import islice

import pymxs
from PySide2 import QtCore
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QAbstractItemView, QFrame, QListWidget, QLabel, QPlainTextEdit, QHBoxLayout, QVBoxLayout, \
    QWidget, QDialog, QPushButton
from pymxs import runtime as mxs


class RootNode(QDialog):
    def __init__(self, parent=QWidget.find(mxs.windows.getMAXHWND())):
        QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setWindowFlags(QtCore.Qt.Window)

        self.resize(240, 360)
        self.setWindowTitle("CAT.RootNode")
        self.mesh = None
        self.rootNode = None
        self.initUI()

        self.selectedNodes = []
        self.skinMeshes = []

        self.addNodes.clicked.connect(self.addNode)
        self.removeNodes.clicked.connect(self.clearNodesInNodeList)
        
        self.addbtn.clicked.connect(self.addMod)
        self.removebtn.clicked.connect(self.removeMod)
        
        self.recreationbtn.clicked.connect(self.recreate)
        self.skinTransfer.clicked.connect(self.startTransfer)

    def clearNodesInNodeList(self):
        self.result = []
        self.writeInNodeList()
        
        
    def startTransfer(self):
        mxs.execute("max create mode")

        with pymxs.undo(True):

            for i in self.skinMeshes:
                skinSource = mxs.skinUtils.ExtractSkinData(i[0])
                skinSource = mxs.getNodeByName(f"SkinData_{i[0].name}")

                count = mxs.skinOps.GetNumberBones(i[1])
                newBones = []

                for item in range(count):
                    # print(item +1, i[0].name, mxs.skinOps.GetBoneNode(i[1], item + 1))
                    try:
                        newBones.append(self.dict[mxs.skinOps.GetBoneNode(i[1], item + 1)])
                    except:
                        pass

                oldSkin = i[1]
                oldSkin.enabled = False

                skinMod = mxs.Skin()
                skinMod.name = "Transdered Skin"

                mxs.addModifier(i[0], skinMod, before=i[2] - 1)

                for bone in newBones:
                    mxs.skinOps.addbone(skinMod, bone, 0)

                mxs.select(i[0])
                mxs.selectmore(skinSource)
                mxs.skinUtils.ImportSkinDataNoDialog(True, False, False, False, False, 1.0, 0)


                mxs.delete(skinSource)
                mxs.clearSelection()

        
        mxs.execute("max modify mode")

    def recreate(self):

        with pymxs.undo(True):
            
            if len(self.result) > 0:

                self.newNodes = []
                self.dict = {}
                temp = mxs.Array()
                lastNode = None
                index = 0

                rootNode = mxs.point()
                rootNode.size = 2
                rootNode.showlinks = True
                rootNode.Box = True
                rootNode.cross = False
                rootNode.axistripod = False
                rootNode.centermarker = False
                mxs.join(temp, rootNode)

            def create_constraints(node, nNode):
                # Position
                sub = mxs.getSubAnim(nNode, 3)
                secsub = mxs.getSubAnim(sub, 1)
                secsub.controller = mxs.Position_List()
                posCtrl = mxs.Position_Constraint()
                thirdsub = mxs.getSubAnim(secsub, 2)
                thirdsub.controller = posCtrl
                posConstraintInterface = posCtrl.constraints
                posConstraintInterface.appendTarget(node, 100)

                # Rotation
                sub = mxs.getSubAnim(nNode, 3)
                secsub = mxs.getSubAnim(sub, 2)
                secsub.controller = mxs.rotation_list()
                posCtrl = mxs.Orientation_Constraint()
                thirdsub = mxs.getSubAnim(secsub, 2)
                thirdsub.controller = posCtrl
                posConstraintInterface = posCtrl.constraints
                posConstraintInterface.appendTarget(node, 100)

            for i in self.result:
                # Create new nodes and add them to list and dict
                nNode = mxs.point()
                nNode.showlinks = True
                nNode.size = 2
                nNode.transform = i.transform
                nNode.name = i.name
                nNode.wireColor = i.wireColor
                self.dict[i] = nNode
                self.newNodes.append(i)

                # Create parent connections
                if mxs.isValidNode(i.parent):
                    nNode.parent = self.dict[i.parent]

                else:
                    nNode.parent = rootNode

                # Create Constraints
                create_constraints(i, nNode)

                # final part
                mxs.join(temp, nNode)
                lastNode = nNode
                index += 1

            mxs.select(temp)

        
        mxs.redrawViews()

    def addMod(self):
        allowed = mxs.readvalue(mxs.StringStream('Skin'))

        if mxs.classOf(mxs.modPanel.getCurrentObject()) == allowed:
            try:
                node = mxs.selection[0]
                mod = mxs.modPanel.getCurrentObject()
                modID = mxs.modPanel.getModifierIndex(mxs.selection[0], mod)

                if [node, mod, modID] in self.skinMeshes:
                    pass
                else:
                    self.skinMeshes.append([node, mod, modID])
                    self.lw_skiin.addItem("{} > {} > ID:{}".format(mxs.selection[0].name, mod, modID))
                    self.lw_skiin.item(self.lw_skiin.count() - 1).setBackground(QColor.fromRgb(60, 60, 60))
            except:
                pass
                # print("Error")

        else:
            pass
            # print("Select Skin Modifier")

    def removeMod(self):
        item = self.lw_skiin.selectedItems()
        allowed = mxs.readvalue(mxs.StringStream('Skin'))


        if mxs.classOf(mxs.modPanel.getCurrentObject()) == allowed:
            try:
                node = mxs.selection[0]
                mod = mxs.modPanel.getCurrentObject()
                modID = mxs.modPanel.getModifierIndex(mxs.selection[0], mod)

                if [node, mod, modID] in self.skinMeshes:
                    print(self.skinMeshes)
                    self.skinMeshes.remove([node, mod, modID])
                    self.lw_skiin.takeItem(self.lw_skiin.row(item[0]))                   
                    print(self.skinMeshes)

                else:
                    print("asdfasdf")
            except:
                
                print("Error")

        else:
            pass
            # print("Select Skin Modifier")
        
        
    def addNode(self):
        # Find Selection as a List
        nodes = mxs.selection

        if len(nodes) > 0:

            mxs.escapeEnable = False

            group_members = []
            group_heads = []
            head_root = []
            nodes_in_chain = []
            independent_nodes = []
            result_list = []
            results_roots = []
            self.ordered_selection_list = []
            self.result = []

            def find_group_members():
                for i in range(len(nodes)):
                    if mxs.isGroupMember(nodes[i]):
                        group_members.append(nodes[i])

            def find_group_heads():

                for i in range(len(nodes)):
                    if mxs.isGroupHead(nodes[i]):
                        group_heads.append(nodes[i])

                if len(group_heads) == 1:
                    head_root.append(group_heads[0])
                    result_list.append(group_heads[0])

                elif len(group_heads) > 1:
                    find_head_roots()

            def find_head_roots():

                for i in range(len(group_heads)):
                    if mxs.isValidNode(group_heads[i].parent) == False or mxs.isGroupMember(group_heads[i]) == False:
                        head_root.append(group_heads[i])
                        result_list.append(group_heads[i])

            def remove_group_members_from_list():
                global out_of_groups
                out_of_groups = []
                for i in range(len(nodes)): out_of_groups.append(nodes[i])
                for i in range(len(nodes)):
                    if mxs.isGroupHead(nodes[i]) or mxs.isGroupMember(nodes[i]):
                        out_of_groups.remove(nodes[i])

            def find_independent_nodes():

                for i in range(len(out_of_groups)):
                    if mxs.isValidNode(out_of_groups[i].parent) == False and out_of_groups[i].children.count == 0:
                        independent_nodes.append(nodes[i])
                        result_list.append(nodes[i])

            def find_node_in_chain():
                for i in range(len(out_of_groups)):
                    if mxs.isValidNode(out_of_groups[i].parent) == True or out_of_groups[i].children.count != 0:
                        nodes_in_chain.append(out_of_groups[i])
                        result_list.append(out_of_groups[i])

            def find_results_roots():

                for i in range(len(result_list)):
                    if mxs.isValidNode(result_list[i].parent) == False or mxs.isValidNode(result_list[i].parent) and \
                            result_list[i].parent not in result_list:
                        # print(f"#{i} - Search root", result_list[i].name)
                        results_roots.append(result_list[i])

            def put_in_ordered_list():

                for i in range(len(results_roots)):
                    self.ordered_selection_list.append(results_roots[i])
                    child_finder(results_roots[i])

            def child_finder(input):
                current = input
                count = input.children.count

                for i in range(count):

                    if current.children[i] in result_list:
                        self.ordered_selection_list.append(current.children[i])
                        # print(current.children[i].name)

                    if current.children[i].children.count != 0:
                        child_finder(current.children[i])

            def filter(input):
                new = []
                allowed = []
                allowed.append(mxs.readvalue(mxs.StringStream('CATBone')))
                allowed.append(mxs.readvalue(mxs.StringStream('HubObject')))

                # print("NOT ALLOWED NODES:")
                index = 0
                for i in input:
                    new.append(i)
                    if mxs.classOf(i) in allowed:
                        self.selectedNodes.append(i)
                        # print("{}".format(index), i.name)
                        index += 1

                # print("{}\n".format(len(self.selectedNodes)))

                self.result = new

            
                self.writeInNodeList(self.result)
                '''
                index = 0
                # print(len(self.result))
                for i in new:

                    self.lw_selectedNodes.addItem(i.name)
                    color = i.wireColor
                    self.lw_selectedNodes.item(index).setBackground(QColor.fromRgb(color.r, color.g, color.b))

                    if ((color.r + color.g + color.b) / 3) > 127.5:
                        self.lw_selectedNodes.item(index).setForeground(QColor.fromRgb(60, 60, 60))
                    else:
                        self.lw_selectedNodes.item(index).setForeground(QColor.fromRgb(240, 240, 240))
                    index += 1
                '''
                
            def debug():
                print(f"#{len(nodes)} | All selected")
                print(f"#{len(nodes_in_chain)} | Node in Chain", nodes_in_chain)
                print(f"#{len(independent_nodes)} | Independent nodes", independent_nodes)
                print(f"#{len(out_of_groups)} | Out of Group", out_of_groups)
                print(f"#{len(group_members)} | Group members", group_members)
                print(f"#{len(group_heads)} | Group heads", group_heads)
                print(f"#{len(head_root)} | Head roots", head_root)
                print(f"#{len(result_list)} | Result", result_list)
                print(f"#{len(results_roots)} | Result roots", results_roots)
                print(f"#{len(self.ordered_selection_list)} | Result in order", self.ordered_selection_list)

            find_group_members()  # 1
            find_group_heads()  # 2
            remove_group_members_from_list()  # 3
            find_independent_nodes()  # 4
            find_node_in_chain()  # 5
            find_results_roots()  # 6
            put_in_ordered_list()  # 7
            filter(self.ordered_selection_list)  # 8
            # debug() # Last

            mxs.escapeEnable = True
            
            
    def writeInNodeList(self, new=[]):
        
        if len(self.result) < 1:
            self.lw_selectedNodes.clear()
            
        index = 0
        # print(len(self.result))
        for i in new:

            self.lw_selectedNodes.addItem(i.name)
            color = i.wireColor
            self.lw_selectedNodes.item(index).setBackground(QColor.fromRgb(color.r, color.g, color.b))

            if ((color.r + color.g + color.b) / 3) > 127.5:
                self.lw_selectedNodes.item(index).setForeground(QColor.fromRgb(60, 60, 60))
            else:
                self.lw_selectedNodes.item(index).setForeground(QColor.fromRgb(240, 240, 240))
            index += 1

    def create(self):
        with pymxs.undo(True):
            def getNode(node, indent='', lastNode=None):
                pass

    def closeDialog(self):
        self.close()

    def initUI(self):

        self.layout = QVBoxLayout()

        self.objectsLayout = QHBoxLayout()
        self.addNodes = QPushButton("Add Nodes")
        self.removeNodes = QPushButton("Clear Nodes")
        self.objectsLayout.addWidget(self.addNodes)
        self.objectsLayout.addWidget(self.removeNodes)

        self.layout.addLayout(self.objectsLayout)

        self.lw_selectedNodes = QListWidget()
        self.layout.addWidget(self.lw_selectedNodes)
        self.lw_selectedNodes.setSelectionMode(QAbstractItemView.NoSelection)

        self.recreationbtn = QPushButton("Recreation")
        self.layout.addWidget(self.recreationbtn)

        line = QFrame()
        line.setMinimumHeight(4)
        line.setStyleSheet("background: #333333")
        self.layout.addWidget(line)

        self.objectsLayout = QHBoxLayout()
        self.addbtn = QPushButton("Add Skin")
        self.removebtn = QPushButton("Remove Skin")

        self.objectsLayout.addWidget(self.addbtn)
        self.objectsLayout.addWidget(self.removebtn)

        self.layout.addLayout(self.objectsLayout)

        self.lw_skiin = QListWidget()
        self.layout.addWidget(self.lw_skiin)
        self.lw_skiin.setMaximumHeight(200)

        line = QFrame()
        line.setMinimumHeight(4)
        line.setStyleSheet("background: #333333")
        self.layout.addWidget(line)

        self.skinTransfer = QPushButton("Skin Transfer")
        self.layout.addWidget(self.skinTransfer)
        self.skinTransfer.setMinimumHeight(32)

        self.setLayout(self.layout)
        self.layout.setMargin(4)


def main():
    widget = RootNode()
    widget.show()


if __name__ == '__main__':
    main()
