from Context import *
from Select import *
from matrix import Vector3, Vector2
from XFormMatrix import BaseXformMatrix
from node import unionBB
from OpenGL.GLU import gluProject
import numpy as np
import mouse
from numpy import pi, tan

def distSqToSegment( p0, p1, q ):
    '''Determines the distance between q and the segment defined by p0 and p1.

    @param:     p0      The first point of the segment (a Vector2).
    @param:     p1      The second point of the segment (a Vector2).
    @param:     q       The query point.
    @returns:   The squared distance of q to p.
    '''
    d = p1 - p0
    q1 = q - p0
    dLenSq = d.lengthSq()
    qLenSq = q1.lengthSq()
    dp = d.dot( q1 )
    if ( dp < 0 ):
        return qLenSq
    elif ( dp > dLenSq ):
        return ( q - p1 ).lengthSq()
    else:
        d_comp = d * ( dp / dLenSq )
        disp = q1 - d_comp
        return disp.lengthSq()
    
class MoveManipulator( SelectContext ):
    '''A manipulator for moving objects in the scene.'''
    def __init__( self ):
        SelectContext.__init__( self )
        self.pivot = Vector3( 0.0, 0.0, 0.0 )
        self.xform = BaseXformMatrix()
        self.highlight = -1
        self.manipulating = False

        self.transScale = 1.0   # the amount of world movement per pixel displacement

        self.xformCache = {}    # the cache of manipulated objects
                                # mapping from object to its original xform
        self.pivotCache = None

    def selectionChanged( self ):
        '''Callback for when the selection changes'''
        minPt = Vector3( 1e6, 1e6, 1e6 )
        maxPt = -minPt
        for item in GLOBAL_SELECTION:
            nMin, nMax = item.getBB()
            minPt, maxPt = unionBB( minPt, maxPt, nMin, nMax )
        self.pivot = ( minPt + maxPt ) * 0.5

    def draw3DGL( self, camControl, select=False ):
        '''Draws the 3D UI elements to the view.

        @param:     camControl      The scene's camera control
        @param:     select          Indicator if this draw call is made for selection purposes
        '''
        self.drawManip( camControl )

    def mousePressEvent( self, event, camControl, scene ):
        '''Handle the mouse press event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = EventReport()
        hasCtrl, hasAlt, hasShift = getModState()
        btns = mouse.mouseButtons()
        if ( GLOBAL_SELECTION and btns == mouse.MIDDLE_BTN ):
            tgtES = camControl.camera.eyespace( self.pivot )
            self.transScale = tgtES.z * tan( camControl.camera.fov * pi / 180.0 * 0.5 )
            self.downScreen = ( event.x(), event.y() )
            self.downPoint = ( 2.0 * event.x() / camControl.VWIDTH - 1.0,
                               2.0 * event.y() / camControl.VHEIGHT - 1.0 )
            self.manipulating = True
            self.manipAxis = None
            if ( self.highlight > -1 ):
                if ( self.highlight == 0 ):
                    self.manipAxis = self.screenAxis( Vector3( 1.0, 0.0, 0.0 ), camControl )
                elif ( self.highlight == 1 ):
                    self.manipAxis = self.screenAxis( Vector3( 0.0, 1.0, 0.0 ), camControl )
                elif ( self.highlight == 2 ):
                    self.manipAxis = self.screenAxis( Vector3( 0.0, 0.0, 1.0 ), camControl )
                lenSq = self.manipAxis.lengthSq()
                self.manipAxis *= 1.0 / lenSq
            for item in GLOBAL_SELECTION:
                self.xformCache[ item ] = item.xform.cache()
            self.pivotCache = self.pivot.copy()
        else:
            result = SelectContext.mousePressEvent( self, event, camControl, scene )
        return result

    def mouseReleaseEvent( self, event, camControl, scene ):
        '''Handle the mouse release event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = EventReport()
        hasCtrl, hasAlt, hasShift = getModState()
        btn = event.button()
        if ( self.manipulating ):
            if ( btn == mouse.MIDDLE_BTN  ):
                self.manipulating = False
                self.xformCache.clear()
                self.downPoint = None
            elif ( btn == mouse.RIGHT_BTN ):
                self.manipulating = False
                self.pivot.set( self.pivotCache )
                for item in GLOBAL_SELECTION:
                    item.xform.setFromCache( self.xformCache[ item ] )
                self.xformCache.clear()
                self.downPoint = None
                result.needsRedraw = True
        else:
            result = SelectContext.mouseReleaseEvent( self, event, camControl, scene )
        return result

    def mouseMoveEvent(  self, event, camControl, scene ):
        '''Handle the mouse move event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     sc      ene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = SelectContext.mouseMoveEvent( self, event, camControl, scene )
        if ( not result.isHandled and GLOBAL_SELECTION ):
            if ( self.manipulating ):
                if ( self.highlight == -1 ):
                    # screen xform
                    currCanonX = 2.0 * event.x() / camControl.VWIDTH - 1.0
                    currCanonY = 2.0 * event.y() / camControl.VHEIGHT - 1.0
                    ar = float( camControl.VWIDTH ) / camControl.VHEIGHT
                    dx = ( currCanonX - self.downPoint[0] ) * self.transScale * ar
                    dy = -( currCanonY - self.downPoint[1] ) * self.transScale 
                    disp = camControl.camera.right * dx + camControl.camera.up * dy
                else:
                    dx = event.x() - self.downScreen[0]
                    dy = self.downScreen[1] - event.y()
                    if ( self.highlight == 0 ):
                        # manip x-axis
                        disp = Vector3( dx * self.manipAxis[0] + dy * self.manipAxis[1], 0.0, 0.0 )
                    elif ( self.highlight == 1 ):
                        # manip y-axis
                        disp = Vector3( 0.0, dx * self.manipAxis[0] + dy * self.manipAxis[1], 0.0 )
                    elif ( self.highlight == 2 ):
                        # manip z-axis
                        disp = Vector3( 0.0, 0.0, dx * self.manipAxis[0] + dy * self.manipAxis[1] )
                self.pivot = self.pivotCache + disp
                for item in GLOBAL_SELECTION:
                    item.xform.setFromCache( self.xformCache[ item ] )
                    item.addTranslation( disp )
                result.needsRedraw = True
            else:
                # confirm modifiers
                projMat = glGetDoublev( GL_PROJECTION_MATRIX )
                viewport = glGetIntegerv( GL_VIEWPORT )
                glPushMatrix()
                self.manipXform( camControl )
                modelMat = glGetDoublev( GL_MODELVIEW_MATRIX )
                glPopMatrix()
                u, v, w = gluProject( 0.0, 0.0, 0.0, modelMat, projMat, viewport )
                ux, vx, wx = gluProject( 1.0, 0.0, 0.0, modelMat, projMat, viewport )
                xDistSq = distSqToSegment( Vector2( u, v ), Vector2( ux, vx ), Vector2( event.x(), camControl.VHEIGHT - event.y() ) )
                ux, vx, wx = gluProject( 0.0, 1.0, 0.0, modelMat, projMat, viewport )
                yDistSq = distSqToSegment( Vector2( u, v ), Vector2( ux, vx ), Vector2( event.x(), camControl.VHEIGHT - event.y() ) )
                ux, vx, wx = gluProject( 0.0, 0.0, 1.0, modelMat, projMat, viewport )
                zDistSq = distSqToSegment( Vector2( u, v ), Vector2( ux, vx ), Vector2( event.x(), camControl.VHEIGHT - event.y() ) )
                dists = np.array( ( xDistSq, yDistSq, zDistSq ) )
                if ( dists.min() < 25 ):
                    h = dists.argmin()
                    result.needsRedraw = self.highlight != h
                    self.highlight = h
                else:
                    result.needsRedraw = self.highlight != -1
                    self.highlight = -1

        return result

    def screenAxis( self, axis, camControl ):
        '''Reports the magnitude of the given manipulator axis in screen space.

        @param:     axis        The axis to determine (x-, y-, or z-axis).
        @param:     camControl  The scene's camera control for this event.
        @returns:   A Vector2 - the vector direction and magnitude of that vector in
                    screen space (size in pixels).
        '''
        projMat = glGetDoublev( GL_PROJECTION_MATRIX )
        viewport = glGetIntegerv( GL_VIEWPORT )
        glPushMatrix()
        self.manipXform( camControl )
        modelMat = glGetDoublev( GL_MODELVIEW_MATRIX )
        glPopMatrix()
        u, v, w = gluProject( 0.0, 0.0, 0.0, modelMat, projMat, viewport )
        ux, vx, wx = gluProject( axis[0], axis[1], axis[2], modelMat, projMat, viewport )
        return Vector2( ux - u, vx - v )
        
    def manipXform( self, camControl ):
        '''Executes the OpenGL commands to set up the manipulator's transform relative to the camera.

        @param:     camControl      The scene's camera control
        '''
        glTranslate( self.pivot.x, self.pivot.y, self.pivot.z )
        scale = 0.2 * ( camControl.camera.pos - self.pivot ).length()
        glScalef( scale, scale, scale )            
            
    def drawManip( self, camControl ):
        '''Draws the manipulator into the scene.

        @param:     camControl      The scene's camera control
        '''
        if ( len( GLOBAL_SELECTION ) > 0 ):
            # TODO: Draw this nicer
            AXES = ( ( 1.0, 0.0, 0.0 ),
                     ( 0.0, 1.0,0.0 ),
                     ( 0.0, 0.0, 1.0 )
                     )
            glPushAttrib( GL_ENABLE_BIT | GL_LINE_BIT )
            glLineWidth( 3.0 )
            glPushMatrix()
            self.manipXform( camControl )
            glDisable( GL_DEPTH_TEST )
            glDisable( GL_LIGHTING )
            glBegin( GL_LINES )
            for i in xrange( 3 ):
                p = AXES[i]
                if ( self.highlight == i ):
                    glColor3f( 1.0, 1.0, 0.0 )
                else:
                    glColor3f( p[0], p[1], p[2] )
                glVertex3f( 0.0, 0.0, 0.0 )
                glVertex3f( p[0], p[1], p[2] )
            glEnd()
            # draw a box right around the pivot
            if ( self.highlight == -1 ):
                glColor3f( 1.0, 1.0, 0.0 )
            else:
                glColor3f( 0.7, 0.7, 0.0 )
            glBegin( GL_LINE_STRIP )
            dx = camControl.camera.right * 0.2
            dy = camControl.camera.up * 0.2
            p = -( dx * 0.5 + dy * 0.5 )
            glVertex3f( p.x, p.y, p.z )
            p += dx
            glVertex3f( p.x, p.y, p.z )
            p += dy
            glVertex3f( p.x, p.y, p.z )
            p -= dx
            glVertex3f( p.x, p.y, p.z )
            p -= dy
            glVertex3f( p.x, p.y, p.z )
            glEnd()
            
            glPopMatrix()
            glPopAttrib()
    