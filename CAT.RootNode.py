from itertools import islice

from PySide2.QtWidgets import QLabel, QPlainTextEdit, QHBoxLayout, QVBoxLayout, QWidget, QDialog, QPushButton
from pymxs import runtime as mxs
import pymxs

class RootNode(QDialog):
    def __init__(self, parent=QWidget.find(mxs.windows.getMAXHWND())):
        QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.Tool)

        self.resize(240, 300)
        self.setWindowTitle("CAT.RootNode")
        self.mesh = None
        self.rootNode = None
        self.initUI()

        self.pickMeshbtn.clicked.connect(self.pickMesh)
        self.pickRootbtn.clicked.connect(self.pickRoot)
        self.start.clicked.connect(self.create)

    def create(self):
        with pymxs.undo(True):
            def getNode(node, indent='', lastNode=None):

                nName = node.name
                nPos = node.transform
                nColor = node.wireColor

                nNode = mxs.point()
                nNode.size = 1

                if lastNode != None:
                    nNode.parent = lastNode

                nNode.showlinks = True
                nNode.name = nName
                nNode.transform = nPos
                nNode.wireColor = nColor

                if mxs.isValidNode(node.parent):
                    lastNode = nNode

                nodeList.append(nNode)

                sub = mxs.getSubAnim(nNode, 3)
                secsub = mxs.getSubAnim(sub, 1)
                secsub.controller = mxs.Position_List()
                posCtrl = mxs.Position_Constraint()
                thirdsub = mxs.getSubAnim(secsub, 2)
                thirdsub.controller = posCtrl
                posConstraintInterface = posCtrl.constraints
                posConstraintInterface.appendTarget(node, 100)

                sub = mxs.getSubAnim(nNode, 3)
                secsub = mxs.getSubAnim(sub, 2)
                secsub.controller = mxs.rotation_list()
                posCtrl = mxs.Orientation_Constraint()
                thirdsub = mxs.getSubAnim(secsub, 2)
                thirdsub.controller = posCtrl
                posConstraintInterface = posCtrl.constraints
                posConstraintInterface.appendTarget(node, 100)

                global index

                if index < 1:
                    rootNode = mxs.point()
                    rootNode.Name = "rootNode"
                    rootNode.wireColor = nColor
                    rootNode.showlinks = True
                    rootNode.size = 1
                    rootNode.position = mxs.point3(0, 0, 0)
                    nNode.parent = rootNode
                    mxs.join(newNodes, rootNode)

                else:
                    mxs.join(newNodes, nNode)

                str = (indent + node.Name)
                first_item = False
                self.reporter.appendPlainText(str)
                self.reporter.repaint()

                index += 1

                for child in node.Children:
                    getNode(child, (indent + '--'), nNode)

            global index
            index = 0
            lastNode = None
            nodeList = []
            newNodes = mxs.Array()
            getNode(self.rootNode)
            mxs.CompleteRedraw()

            self.reporter.appendPlainText("Recreation Is Finished")
            self.reporter.repaint()

            self.reporter.appendPlainText("Find Mesh Old Skin")
            self.reporter.repaint()
            mesh = self.mesh
            oldSkin = mesh.modifiers[0]
            oldSkin.enabled = False
            self.reporter.appendPlainText("Old Skin Disabled")
            self.reporter.repaint()
            self.reporter.appendPlainText("Extract Skin Data")
            self.reporter.repaint()
            skinSource = mxs.skinUtils.ExtractSkinData(mesh)
            skinSource = mxs.getNodeByName(f"SkinData_{self.mesh.name}")
            self.reporter.repaint()

            self.reporter.appendPlainText("Create New Skin")
            self.reporter.repaint()
            skinMod = mxs.Skin()
            mxs.addModifier(mesh, skinMod)

            self.reporter.appendPlainText("Adding Bones To Skin")
            self.reporter.repaint()
            for i in islice(newNodes, 1, None):
                mxs.skinOps.addbone(skinMod, i, 0)

            self.reporter.appendPlainText("Matching By Name")
            self.reporter.repaint()
            mxs.select(mesh)
            mxs.selectmore(skinSource)
            mxs.skinUtils.ImportSkinDataNoDialog(True, False, False, False, False, 1.0, 0)

            mxs.delete(skinSource)
            mxs.clearSelection()

            self.reporter.appendPlainText("\nDone!")
            self.reporter.repaint()


    def pickMesh(self):
        self.mesh = None
        self.pickMeshbtn.setText("Mesh:...")
        self.reporter.appendPlainText("Select The Mesh In The Scene")
        self.mesh = mxs.pickObject()

        if self.mesh:
            self.pickMeshbtn.setText(f"Mesh:{self.mesh.name}")
            self.reporter.appendPlainText(f'"{self.mesh.name}" Is Selected')
        else:
            self.mesh = None
            self.pickMeshbtn.setText("Mesh")
            self.reporter.appendPlainText(f"Cancel")

    def pickRoot(self):
        self.rootNode = None
        self.pickRootbtn.setText("Root:...")
        self.reporter.appendPlainText("Select The Root Node Of CAT")
        self.rootNode = mxs.pickObject()

        if self.rootNode:
            self.pickRootbtn.setText(f"Root:{self.rootNode.name}")
            self.reporter.appendPlainText(f'"{self.rootNode.name}" Is Selected')
        else:
            self.rootNode = None
            self.pickRootbtn.setText("Root Node")
            self.reporter.appendPlainText(f"Cancel")

    def closeDialog(self):
        self.close()

    def initUI(self):

        self.layout = QVBoxLayout()

        self.objectsLayout = QHBoxLayout()
        self.pickRootbtn = QPushButton("Root Node")
        self.pickMeshbtn = QPushButton("Mesh")

        self.objectsLayout.addWidget(self.pickRootbtn)
        self.objectsLayout.addWidget(self.pickMeshbtn)

        self.layout.addLayout(self.objectsLayout)

        self.reporter = QPlainTextEdit()
        self.layout.addWidget(self.reporter)

        self.start = QPushButton("Start")
        self.layout.addWidget(self.start)

        label = QLabel()
        label.setText("<a href=\"https://www.artstation.com/shirzadbh/store\">By: Shirzad Bahrami</a>")
        label.setOpenExternalLinks(True)

        self.layout.addWidget(label)
        self.setLayout(self.layout)
        self.layout.setMargin(4)


def main():
    widget = RootNode()
    widget.show()


if __name__ == '__main__':
    main()
