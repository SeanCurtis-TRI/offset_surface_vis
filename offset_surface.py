# A simple application for playing with offset surfaces.

import os
import sys

if ( sys.version_info[0] != 2 ):
    print( "This only works with Python version 2.*" )
    raise Exception("Unsupported python version")

from PyQt4 import QtCore, QtGui
##from Context import SelectContext
from manipulator import OffsetManipulator
from GLWidget import GLWidget
from scene import Scene
import mouse
import key as keys

class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("offset surface visualization")
        
        self.last_dir = '.'  # the last directory read from.

        mainFrame = QtGui.QFrame( self )
        
        self.scene = Scene()
        self.manip = OffsetManipulator()
        self.scene.context = self.manip
        self.glWidget = GLWidget( self.scene )

        mainLayout = QtGui.QVBoxLayout( mainFrame )
        mainLayout.addWidget(self.glWidget)
        mainLayout.setStretch( 0, 1 )

        fileMenu = self.menuBar().addMenu( "File" )
        open_obj = QtGui.QAction("Open &Obj", self, statusTip="Select OBJ file to load",
                                 triggered=self.spawnOpenFileDlg, shortcut="Ctrl+o")
        clear = QtGui.QAction("&Clear", self, statusTip="Clear the scene",
                                 triggered=self.clear, shortcut="Ctrl+x")
        fileMenu.addAction( open_obj )
        fileMenu.addAction( clear )
        self.setCentralWidget( mainFrame )

    def clear( self ):
        self.glWidget.clear_nodes()
        self.manip.clear_object()
        
    def spawnOpenFileDlg( self ):
        fileName = QtGui.QFileDialog.getOpenFileName( self, "Read OBJ file",
                                                      self.last_dir, "OBJ files (*.obj)" )
        if ( fileName ):
            self.clear()
            self.glWidget.addObjToScene( fileName )
            self.manip.set_object( self.scene.nodes[-1] )
            path, fName = os.path.split( str( fileName ) )
            self.last_dir = path
    
if __name__ == '__main__':
    print QtCore.qVersion()
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
