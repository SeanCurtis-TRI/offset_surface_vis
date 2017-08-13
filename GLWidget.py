# definition of the IVT GLWidget

from PyQt4 import QtCore, QtGui, QtOpenGL
from OpenGL.GL import *
import math
from camera import GLCamera
from mesh import getMeshNode
from camControl import OrbitCamControl
from matrix import Vector3
from Context import EventReport
from material import Material
import mouse

class GLWidget( QtOpenGL.QGLWidget ):
    def __init__(self, scene, parent=None):
        '''Constructor.

        @param      scene       A Scene instance.
        @param      parent      An optional parent node.
        '''
        super(GLWidget, self).__init__(parent)

        self.scene = scene
        camera = GLCamera( pos=Vector3( 0.5, 0.5, -3 ) )
        self.camControl = OrbitCamControl( camera, Vector3( 0.0, 0.0, 0.0 ) )

        self.hidden = False
        self.bgColor = ( 0.3, 0.35, 0.4, 0.0 )
        self.setFocusPolicy( QtCore.Qt.StrongFocus )
        self.setMouseTracking( True )

    def addObjToScene( self, obj_filename ):
        '''Adds the given obj file to the scene.'''
        self.scene.addNode( getMeshNode( obj_filename ) )
        self._aimAtCenter()

    def addObjsToScene( self, obj_filenames ):
        for obj_filename in obj_filenames:
            self.scene.addNode( getMeshNode( obj_filename ) )
        self._aimAtCenter()

    def clear_nodes( self ):
        '''Clears the scene'''
        self.scene.clear_nodes()
        self.update()

    def _aimAtCenter( self ):
        '''Aims the camera at the center of the scene.'''
        center = self.scene.center()
        self.camControl.setTarget( center )
        self.update()
        
    def minimumSizeHint(self):
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        return QtCore.QSize(400, 400)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace( GL_BACK )
        glClearColor( self.bgColor[0], self.bgColor[1], self.bgColor[2], self.bgColor[3] )

        # lighting
        LightAmbient  = [ 0.05, 0.05, 0.05, 1.0]
        LightDiffuse  = [ 0.85, 0.85, 0.85, 1.0]
        # 4th position 0 --> directional, 1 --> point light
        LightPosition = [ 0, 0, 1, 0.0]
        glLightfv( GL_LIGHT1, GL_AMBIENT, LightAmbient )
        glLightfv( GL_LIGHT1, GL_DIFFUSE, LightDiffuse )
        glLightfv( GL_LIGHT1, GL_POSITION, LightPosition )
        glLightfv( GL_LIGHT1, GL_SPECULAR, [0.0, 0.0, 1.0, 0.0] )
        glEnable( GL_LIGHT1 )
        glEnable( GL_LIGHTING )
        glShadeModel(GL_FLAT)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
        glLoadIdentity()
        self.camControl.setGLView()
        if ( self.hidden ):
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
            glPushMatrix()
            push = self.camControl.forward() * 0.005
            glTranslatef( push.x, push.y, push.z )
            glColor4fv( self.bgColor )
            self.scene.drawGL( self.camControl )    # TODO: Skip the context on this pass
            glPopMatrix()
            Material.setGL = Material.setGLHidden
            glColor3f( 1.0, 1.0, 1.0 )
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
        else:
            glColor3f( 0.9, 0.9, 0.9 )
        self.scene.drawGL( self.camControl )
        self.camControl.drawGL()
        if ( self.hidden ):
            Material.setGL = Material.setGLSolid

    def resizeGL(self, width, height):
        side = min(width, height)
        if side < 0:
            return

        glViewport((width - side) // 2, (height - side) // 2, side, side)
        self.camControl.setProjection( width, height )

    def keyPressEvent( self, event ):
        if ( event.key() == QtCore.Qt.Key_H ):
            self.hidden = not self.hidden
            if ( self.hidden ):
                glDisable( GL_LIGHTING )
            else:
                glEnable( GL_LIGHTING )
                glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
            self.updateGL()
        else:
            result = self.camControl.keyPressEvent( event, self.scene )
            if ( self.scene and not result.isHandled ):
                result = self.scene.keyPressEvent( event, self.camControl )        
            if ( result.needsRedraw ):
                self.updateGL()
            if ( not result.isHandled ):
                super( GLWidget, self ).keyPressEvent( event ) 
        
    def keyReleaseEvent( self, event ):
        result = self.camControl.keyReleaseEvent( event, self.scene )
        if ( self.scene and not result.isHandled ):
            result = self.scene.keyReleaseEvent( event, self.camControl )       
            
        if ( result.needsRedraw ):
            self.updateGL()
        
    def mousePressEvent( self, event ):
        mouse.buttonDown( event.button() )
        result = self.camControl.mousePressEvent( event, self.scene )
        if ( self.scene and not result.isHandled ):
            result = self.scene.mousePressEvent( event, self.camControl )
        if ( result.needsRedraw or result.sceneUpdate ):
            self.updateGL()

    def mouseReleaseEvent( self, event ):
        mouse.buttonUp( event.button() )
        result = self.camControl.mouseReleaseEvent( event, self.scene )
        if ( self.scene and not result.isHandled ):
            result = self.scene.mouseReleaseEvent( event, self.camControl )
        if ( result.needsRedraw or result.sceneUpdate ):
            self.updateGL()

    def mouseMoveEvent(self, event):
        result = self.camControl.mouseMoveEvent( event, self.scene )
        if ( self.scene and not result.isHandled ):
            result = self.scene.mouseMoveEvent( event, self.camControl )
        if ( result.needsRedraw or result.sceneUpdate ):
            self.updateGL()
