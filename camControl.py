# camera controllers for the OpenGL window

from camera import *
import mouse
from numpy import tan, pi
import key as keys
import numpy as np
from Context import EventReport
import Select
import node

class CamControlException( Exception ):
    '''Base exception for camera controls'''
    pass

def cross():
    '''print draws a cross'''
    glBegin( GL_LINES )
    glVertex3f( -1.0, 0.0, 0.0 )
    glVertex3f( 1.0, 0.0, 0.0 )
    glVertex3f( 0.0, -1.0, 0.0 )
    glVertex3f( 0.0, 1.0, 0.0 )
    glVertex3f( 0.0, 0.0, 1.0 )
    glVertex3f( 0.0, 0.0, -1.0 )
    glEnd()
    
class CameraControl:
    '''The base class for camera control'''
    # TODO: This is BAD
    #   It doesn't allow for multiple viewports in the physical window
    #   I really need to have this set from a logical viewport.
    
    VWIDTH = 0     # the viewport width
    VHEIGHT = 0    # the viewport height
    
    def __init__( self, camera ):
        self.camera = camera
        # the history of controller manipulations
        self.past = []
        self.future = []

    # OPERATIONS ON CAMERA PROPERTIES
    def setProjection( self, width, height ):
        '''Sets the view size for the projection matrix.

        @param:     width       The view width.
        @param:     height      The view height.
        '''
        self.VWIDTH = width
        self.VHEIGHT = height
        self.camera.setProjection( width, height )

    def setGLView( self ):
        '''Uses the camera to set the OpenGL context'''
        self.camera.setGLView()

    def setSelectMat( self, selectPoint, pickSize=5 ):
        '''Given the selection point, computes the projection matrices for the
        selection matrix.

        @param:     selectPoint     The point, in screen space, at which the selection is occuring.
        @param:     pickSize        The size of the box that selectables will be considered.
        '''
        self.camera.setSelectMat( selectPoint, self.VWIDTH, self.VHEIGHT, pickSize )

    def setSelectMatRegion( self, x0, y0, x1, y1 ):
        '''Given the selection point, computes the projection matrices for the
        selection matrix.

        @param:     x0          The minimum x-value of the rectangular region.
        @param:     y0          The minimum y-value of the rectangular region.
        @param:     x1          The maximum x-value of the rectangular region.
        @param:     y1          The amximum y-value of the rectangular region.
        '''
        self.camera.setSelectMatRegion( x0, y0, x1, y1, self.VWIDTH, self.VHEIGHT )

    def forward( self ):
        '''Reports the camera's forward direction.

        @returns:       A Vector3 representing the camera's facing direction.
        '''
        return self.camera.facing

    def right( self ):
        '''Reports the camera's right direction.

        @returns:       A Vector3 representing the camera's right direction.
        '''
        return self.camera.right

    def up( self ):
        '''Reports the camera's  up direction.

        @returns:       A Vector3 representing the camera's  up direction.
        '''
        return self.camera.up
    
    def state( self, camera ):
        '''Returns a 2-tuple of state representing the controller and camera state.

        If a child class camera controller has data that it needs to stash, it should override this class.
        The state it returns should be a 2-tuple consiting of ( ( child class state ), parent-class state ).
        First it constructs a tuple of all the state the child class uniquely cares about.  It combines that
        into a 2-tuple with the second element being the state returned by calling the parent class's
        state method.

        @param:         camera      The camera to include in the state.
        @returns:       A tuple of state representing the minimum data to uniquely represent the camera's state.
        '''
        return ( camera, )

    def setState( self, state ):
        '''Sets the camera controller from the given state tuple.

        If a child class has state that must be stashed, it is responsible for overriding this function.
        The input should be a 2-tuple (the 2-tuple created by the child class's implemetnation of state).
        The class should expand the first element in the 2-tuple to set its state and then call the parent
        class's implementation of setState with the second element in the tuple.

        @param:     state       A tuple consisting of nested tuples sufficient to restore the
                                controller state to this controller and all parent classes.
        '''
        self.camera = state[0]
        assert( isinstance( self.camera, GLCamera ) )
    
    def record( self, camera ):
        '''Pushes the current camera onto the stack'''
        self.past.append( self.state( camera ) )
        if ( self.future ):
            # performing a new operation invalidates the old future.
            self.future = []

    def popHistory( self ):
        '''Pops the last camera state in the history from the stack and returns it.

        @returns:       The last camera state stored.  None if there is no state.
        '''
        if ( self.past ):
            return self.past.pop( -1 )
        else:
            return None

    def viewBack( self ):
        '''Sets the camera controller back one state in the view history.

        If there are no previous views, a CamControlException is thrown.
        '''
        if ( not self.past ):
            raise CamControlException
        self.future.append( self.state( self.camera ) )
        self.setState( self.past.pop( -1 ) )

    def viewForward( self ):
        '''Sets the camera controller forward one state in the view history.

        If there are no "future" views, a CamControlException is thrown.
        Future views exist because multiple camera manipulations have been performed,
        and then the user has stepped back in history.
        '''
        if ( not self.future ):
            raise CamControlException
        self.past.append( self.state( self.camera ) )
        self.setState( self.future.pop( -1 ) )
        
    def drawGL( self ):
        '''Default camera control visualization'''
        pass
    
    def keyPressEvent( self, event, scene ):
        '''Processes a key pressed event.

        @param:     event       The event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An EventReport indicating the control's event response.
        '''
        result = EventReport()
        key = event.key()
        if ( key == keys.RIGHT_BRACKET ):
            try:
                self.viewForward()
                result.needsRedraw = True
            except CamControlException:
                pass
            result.isHandled = True
        elif ( key == keys.LEFT_BRACKET ):
            try:
                self.viewBack()
                result.needsRedraw = True
            except CamControlException:
                pass
            result.isHandled = True

        return result

    def keyReleaseEvent( self, event, scene ):
        '''Processes a key release event.

        @param:     event       The event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An EventReport indicating the control's event response.
        '''
        return EventReport()

class ZeroWorkCamControl( CameraControl ):
    '''The zero-work camera control works by caching the initial manipulation state
    (camera configuration and mouse down position at start of manipulation) and
    computes transformations relative to this initial state.

    Sub-classes which include additional state are responsible for caching any additional
    data to do its work.
    '''
    def __init__( self, camera ):
        '''Constructor'''
        CameraControl.__init__( self, camera )
        # TODO: This heavily implies MOUSE, I should factor the mouse out so that
        #   other manipulators can be used.
        # 2-tuple of ints, the position, in screen space, of the mouse at the
        #   beginning of the camera manipulation
        self.downScreen = None
        self.downCamera = None

    def mousePressEvent( self, event, scene ):
        '''Handles a mouse button press event.

        @param:     event       The mouse press event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An instance of EventReport indicating how the event was handled.
        '''
        pass

    def mouseMoveEvent( self, event, scene ):
        '''Handles a mouse move event.

        @param:     event       The mouse move event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An instance of EventReport indicating how the event was handled.
        '''
        pass

    def mouseReleaseEvent( self, event, scene ):
        '''Handles a mouse button release event.

        @param:     event       The mouse release event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An instance of EventReport indicating how the event was handled.
        '''
        pass

class OrbitCamControl( ZeroWorkCamControl ):
    '''The camera control that orbits around a target point.'''
    # The types of camera motion
    NO_MOVEMENT = 0
    TRANS = 1   # translate the camera on its local facing plane (moving target with it)
    ORBIT = 2   # rotate around the target (target remains unchanged)
    DOLLY = 4   # move in and out toward the target (target remains unchanged)
    MOVING = 7  # mask for indicating current operation
    READY = 8   # Indicates that it is ready to move

    DISPLAY_SIZE = 0.1
    
    def __init__( self, camera, target ):
        ZeroWorkCamControl.__init__( self, camera )
        # the target for the camera.
        self.target = target
        # aim camera at target
        try:
            self.camera.lookAt( self.target )
        except CameraException as e:
            print( "OrbitCamControl has an error: {0}. Perturbing target point by 1 meter in the facing direction.".format( e ) )
            self.target += self.camera.facing
            # THIS time if an exception gets thrown, it is a catastrophic failure that should percolate up.
            self.camera.lookAt( self.target )

        self.moving = self.NO_MOVEMENT
        self.downTarget = None

        # cached values for particular operations
        # Translation
        self.transScale = 0.0
        # Dolly
        self.maxDolly = 0.0
        # in order to know what the full keyboard state is, I need to know which
        #   keys are pressed
        self.pressed = set()

    def moveReady( self ):
        '''Examines the mouse state and determines if the keyboard modifiers are
            such that a left-drag will produce camera movement.

        @returns:       An int.  The encoded enumeration which indicates the movement
                        state.
        '''
        hasCtrl, hasAlt, hasShift = mouse.getModState()
        buttons = mouse.mouseButtons()
        orbit = hasAlt and buttons == mouse.LEFT_BTN and not ( hasCtrl or hasShift )
        pan = hasAlt and buttons == mouse.MIDDLE_BTN and not ( hasCtrl or hasShift )
        dolly = hasAlt and buttons == ( mouse.RIGHT_BTN ) and not ( hasCtrl or hasShift )

        return self.moveType( pan, orbit, dolly )

    def drawGL( self ):
        '''Draws camera control functionality to the screen'''
        if ( self.moving ):
            if ( self.moving == self.TRANS ):
                self.drawTrans()
            elif ( self.moving == self.ORBIT ):
                self.drawOrbit()
            elif ( self.moving == self.DOLLY ):
                self.drawDolly()

    def drawTrans( self ):
        '''Draws ornamentation for performing translation'''
        glPushMatrix()

        glPushAttrib( GL_LINE_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT )
        glDisable( GL_DEPTH_TEST )
        glDisable( GL_LIGHTING )

        rot = ( self.camera.right.x, self.camera.right.y, self.camera.right.z, 0.0,
                self.camera.up.x, self.camera.up.y, self.camera.up.z, 0.0,
                self.camera.right.x, self.camera.right.y, self.camera.right.z, 0.0,
                0.0, 0.0, 0.0, 1.0 )
        p = self.camera.pos + self.camera.facing
        glTranslatef( p.x, p.y, p.z )
        glMultMatrixf( rot )
        glLineWidth( 4.0 )
        glColor3f( 1.0, 0.5, 0.5 )

        P0 = Vector3( 0.0, self.DISPLAY_SIZE, 0.0 )
        P1 = Vector3( -self.DISPLAY_SIZE * 0.25, self.DISPLAY_SIZE * 0.5, 0.0 )
        P2 = Vector3( -self.DISPLAY_SIZE * 0.125, self.DISPLAY_SIZE * 0.5, 0.0 )
        P3 = Vector3( -self.DISPLAY_SIZE * 0.125, self.DISPLAY_SIZE * 0.125, 0.0 )
        glBegin( GL_LINE_STRIP ) # 25 vertices
        glVertex3f( P0.x, P0.y, P0.z )
        glVertex3f( P1.x, P1.y, P1.z )
        glVertex3f( P2.x, P2.y, P2.z )
        
        glVertex3f( P3.x, P3.y, P3.z )

        glVertex3f( -P2.y, -P2.x, P2.z )
        glVertex3f( -P1.y, -P1.x, P1.z )
        glVertex3f( -P0.y, -P0.x, P0.z )
        glVertex3f( -P1.y, P1.x, P1.z )
        glVertex3f( -P2.y, P2.x, P2.z )
        
        glVertex3f( P3.x, -P3.y, P3.z )

        glVertex3f( P2.x, -P2.y, P2.z )
        glVertex3f( P1.x, -P1.y, P1.z )
        glVertex3f( P0.x, -P0.y, P0.z )
        glVertex3f( -P1.x, -P1.y, P1.z )
        glVertex3f( -P2.x, -P2.y, P2.z )
        
        glVertex3f( -P3.x, -P3.y, P3.z )

        glVertex3f( P2.y, P2.x, P2.z )
        glVertex3f( P1.y, P1.x, P1.z )
        glVertex3f( P0.y, -P0.x, P0.z )
        glVertex3f( P1.y, -P1.x, P1.z )
        glVertex3f( P2.y, -P2.x, P2.z )
        
        glVertex3f( -P3.x, P3.y, P3.z )
        
        glVertex3f( -P2.x, P2.y, P2.z )
        glVertex3f( -P1.x, P1.y, P1.z )
        glVertex3f( -P0.x, P0.y, P0.z )

        glEnd()
        glPopAttrib()
        
        glPopMatrix()

    def drawDolly( self ):
        '''Draws ornamentation for performing translation'''
        glPushMatrix()

        glPushAttrib( GL_LINE_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT )
        glDisable( GL_DEPTH_TEST )
        glDisable( GL_LIGHTING )

        rot = ( self.camera.right.x, self.camera.right.y, self.camera.right.z, 0.0,
                self.camera.up.x, self.camera.up.y, self.camera.up.z, 0.0,
                self.camera.right.x, self.camera.right.y, self.camera.right.z, 0.0,
                0.0, 0.0, 0.0, 1.0 )
        p = self.camera.pos + self.camera.facing
        glTranslatef( p.x, p.y, p.z )
        glMultMatrixf( rot )
        glScale( 1.0, 0.5, 1.0 )
        glLineWidth( 4.0 )
        glColor3f( 1.0, 0.5, 0.5 )

        P0 = Vector3( 0.0, self.DISPLAY_SIZE , 0.0 )
        P1 = Vector3( -self.DISPLAY_SIZE * 0.5, self.DISPLAY_SIZE * 0.5, 0.0 )
        P2 = Vector3( -self.DISPLAY_SIZE * 0.25, self.DISPLAY_SIZE * 0.5, 0.0 )
        P3 = Vector3( -self.DISPLAY_SIZE * 0.5, 0.0, 0.0 )
        P4 = Vector3( -self.DISPLAY_SIZE , 0.0, 0.0 )
        P5 = Vector3( 0.0, -self.DISPLAY_SIZE, 0.0 )
        
        glBegin( GL_LINE_STRIP ) # 25 vertices
        glVertex3f( P0.x, P0.y, P0.z )
        glVertex3f( P1.x, P1.y, P1.z )
        glVertex3f( P2.x, P2.y, P2.z )
        glVertex3f( P3.x, P3.y, P3.z )
        glVertex3f( P4.x, P4.y, P4.z )
        glVertex3f( P5.x, P5.y, P5.z )
        glVertex3f( -P4.x, P4.y, P4.z )
        glVertex3f( -P3.x, P3.y, P3.z )
        glVertex3f( -P2.x, P2.y, P2.z )
        glVertex3f( -P1.x, P1.y, P1.z )
        glVertex3f( P0.x, P0.y, P0.z )
        glEnd()
        glPopAttrib()
        
        glPopMatrix()

    def drawOrbit( self ):
        '''Draws ornamentation for performing translation'''
        glPushMatrix()

        glPushAttrib( GL_LINE_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT )
        glDisable( GL_DEPTH_TEST )
        glDisable( GL_LIGHTING )

        p = self.camera.pos + self.camera.facing
        glTranslatef( p.x, p.y, p.z )

        glLineWidth( 4.0 )
        glColor3f( 1.0, 0.5, 0.5 )

        SAMPLES = 16
        t = np.linspace( 0.0, 2.0 * np.pi, SAMPLES + 1 )
        x = np.cos( t )
        y = np.sin( t )
        
        glScalef( self.DISPLAY_SIZE, self.DISPLAY_SIZE, self.DISPLAY_SIZE )
        glColor3f( 0.4, 1.0, 0.4 )
        glBegin( GL_LINE_STRIP )
        for i in xrange( len( t ) ):
            glVertex3f( x[i], 0.0, y[i] )
        glVertex3f( x[0], 0.0, y[0] )
        glEnd()

        glColor3f( 0.4, 0.4, 1.0 )
        glBegin( GL_LINE_STRIP )
        for i in xrange( len( t ) ):
            glVertex3f( x[i], y[i], 0.0 )
        glVertex3f( x[0], y[0], 0.0 )
        glEnd()
        
        glColor3f( 1.0, 0.4, 0.4 )
        glBegin( GL_LINE_STRIP )
        for i in xrange( len( t ) ):
            glVertex3f( 0.0, x[i], y[i] )
        glVertex3f( 0.0, x[0], y[0] )
        glEnd()
        
        glPopAttrib()
        
        glPopMatrix()

    def drawTarget( self ):
        '''Draws a cross hairs at the target'''
        glPushAttrib( GL_LINE_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT )
        glDisable( GL_DEPTH_TEST )
        glDisable( GL_LIGHTING )
        glLineWidth( 2.0 )
        glColor3f( 1.0, 1.0, 0.0 )
        glBegin( GL_LINES )
        p1 = self.target - self.camera.up
        p2 = self.target + self.camera.up
        glVertex3f( p1.x, p1.y, p1.z )
        glVertex3f( p2.x, p2.y, p2.z )
        p1 = self.target - self.camera.right
        p2 = self.target + self.camera.right
        glVertex3f( p1.x, p1.y, p1.z )
        glVertex3f( p2.x, p2.y, p2.z )
        glEnd()
        glPopAttrib()

    def moveType( self, pan, orbit, dolly ):
        '''Specifies the move type from a set of booleans.

        One and only one of the booleans should be true.
        
        @param:     pan         A boolean indicating if panning is the work.
        @param:     orbit       A boolean indicating if tilting is the work.
        @param:     dolly       A boolean indicating if dollying is the work.
        '''
        return ( pan << 0 ) | ( orbit << 1 ) | ( dolly << 2 ) 

    def mousePressEvent( self, event, scene ):
        '''Handles a mouse button press event.

        @param:     event       The mouse press event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An instance of EventReport indicating how the event was handled.
        '''
        result = EventReport()
        btn = event.button()

        move = self.moveReady()
        
        if ( move ):
            if ( self.moving & self.MOVING ):
                # stop the motion - it must have changed
                self.finish()
                result.isHandled = True
                result.needsRedraw = True
            else:            
                if ( move == self.TRANS ):
                    tgtES = self.camera.eyespace( self.target )
                    self.transScale = tgtES.z * tan( self.camera.fov * pi / 180.0 * 0.5 )
                    # For translation, this is actually the parameterized
                    #   position of the mouse point in screen space
                    #   each dimension lies in the range [-1, 1]
                    self.downScreen = ( 2.0 * event.x() / self.VWIDTH - 1.0,
                                        2.0 * event.y() / self.VHEIGHT - 1.0 )
                elif ( move == self.DOLLY ):
                    dist = self.camera.distance( self.target )
                    self.maxDolly = dist - 0.01 # TODO: Replace this with the nearplane
                    self.downScreen = ( event.x(), event.y() )
                elif ( move == self.ORBIT ):
                    self.downScreen = ( event.x(), event.y() )
                self.moving = self.READY
                self.downCamera = self.camera.copy()
                self.downTarget = self.target.copy()
            result.isHandled = True
        elif ( self.moving and btn == mouse.RIGHT_BTN ):
            # test to see if valid keys are still held and move from moving to display
            self.camera.setFrom( self.downCamera )
            self.target.set( self.downTarget )
            self.moving = self.NO_MOVEMENT
            self.downCamera = None
            self.downTarget = None
            result.needsRedraw = True
            result.isHandled = True
        return result            

    def cameraTrans( self, horizontal, vertical ):
        '''Performs the translation of the camera.

        @param:     horizontal      The amount of horizontal motion.
        @param:     vertical        The amount of vertical motion.
        '''
        # restore the original camera - transfrom from starting point.
        self.camera.setFrom( self.downCamera )
        # now move the camera
        m = self.camera.truckPedastal( horizontal, vertical )
        self.target.set( m.transform( self.downTarget ) )

    def cameraDolly( self, amount ):
        '''Performs the camera dolly movement.

        @param:     amount          The signed amount of dolly motion.
        @param:     Returns True if the camera moved (and a redraw is necessary)
                    False otherwise.
        '''
        self.camera.setFrom( self.downCamera )
        if ( amount > self.maxDolly ):
            amount = self.maxDolly
        if ( amount ):
            m = self.camera.dolly( amount )
            return True
        return False

    def cameraOrbit( self, pan, tilt ):
        '''Performs the camera orbit movement.

        @param:     pan         The pan amount.
        @param:     tilt        The tilt amount.
        '''
        self.camera.setFrom( self.downCamera )
        self.camera.orbit( pan, tilt, self.downTarget )

    def mouseMoveEvent( self, event, scene ):
        '''Handles a mouse move event.

        @param:     event       The mouse move event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An instance of EventReport indicating how the event was handled.
        '''
        result = EventReport()
        if ( self.moving == self.READY ):
            self.moving = self.moveReady()
        if ( self.downCamera ):
            result.isHandled = True
            if ( self.moving == self.TRANS ):
                currCanonX = 2.0 * event.x() / self.VWIDTH - 1.0
                currCanonY = 2.0 * event.y() / self.VHEIGHT - 1.0

                ar = float( self.VWIDTH ) / self.VHEIGHT
                dx = ( currCanonX - self.downScreen[0] ) * self.transScale * ar
                dy = ( currCanonY - self.downScreen[1] ) * self.transScale 

                self.cameraTrans( -dx, dy )
                result.needsRedraw = True
            elif ( self.moving == self.ORBIT ):
                SCALE = 0.01
                dy = ( self.downScreen[1] - event.y() ) * SCALE
                dx = ( event.x() - self.downScreen[0] ) * SCALE
                self.cameraOrbit( -dx, dy )
                result.needsRedraw = True
            elif ( self.moving == self.DOLLY ):
                dy = self.downScreen[1] - event.y()
                result.needsRedraw = self.cameraDolly( dy * 0.1 )   # TODO: Get rid of this magic number
        return result

    def mouseReleaseEvent( self, event, scene ):
        '''Handles a mouse button release event.

        @param:     event       The mouse release event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An instance of EventReport indicating how the event was handled.
        '''
        btn = event.button()
            
        result = EventReport()
        if ( self.moving & self.MOVING ):
            move = self.moveReady()
            if ( move != self.moving ):
                self.finish()
                result.isHandled = True
                result.needsRedraw = True
                if ( move ):
                    self.moving = self.READY
                else:
                    self.moving = self.NO_MOVEMENT
            
        return result

    def finish( self ):
        '''Ends the movement operation'''
        self.moving = self.NO_MOVEMENT
        self.record( self.downCamera )
        self.downCamera = None
        self.downTarget = None

    def setTarget( self, pos ):
        '''Translates the camera and target such that the target as at pos, and the camear-target
            relationship is maintained.'''
        delta = pos - self.target
        self.target.set( pos )
        self.camera.pos += delta

    def keyPressEvent( self, event, scene ):
        '''Processes a key pressed event.

        @param:     event       The event.
        
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An EventReport indicating the control's event response.
        '''
        result = ZeroWorkCamControl.keyPressEvent( self, event, scene )
        if ( not result.isHandled ):
            hasCtrl, hasAlt, hasShift = mouse.getModState()
            noMods = not ( hasCtrl or hasAlt or hasShift )
            key = event.key()
            if ( key == keys.K_f and noMods ):
                result.isHandled = True
                result.needsRedraw = self.frameOnSelected( scene )
            elif ( key == keys.K_a and noMods ):
                result.isHandled = True
                result.needsRedraw = self.frameOnAll( scene )
            
        return result

    def frameOnSelected( self, scene ):
        '''Reposition camera and target so that selected elements are tightly bounded.
        
        @param:     scene       An instance of Scene -- the scene being interacted with.
        '''
        if ( Select.GLOBAL_SELECTION ):
            minPt = Vector3( 1e6, 1e6, 1e6 )
            maxPt = -minPt
            for item in Select.GLOBAL_SELECTION:
                iMin, iMax = item.getBB()
                minPt, maxPt = node.unionBB( minPt, maxPt, iMin, iMax )
            return self._frame( minPt, maxPt )
        else:
            return self.frameOnAll( scene )        

    def frameOnAll( self, scene ):
        '''Reposition camera and target so that all elements are tightly bounded.
        
        @param:     scene       An instance of Scene -- the scene being interacted with.
        '''
        minPt, maxPt = scene.getBB()
        return self._frame( minPt, maxPt )

    def _frame( self, bbMin, bbMax ):
        '''Reposition the camera so that the bounding box is tightly bounded.

        @param:     bbMin       The minimum coordinates of the axis-aligned bounding box (in world space).
        @param:     bbMax       The maximum coordinates of the axis-aligned bounding box (in world space).
        @returns:   True if the camera moved, False otherwise.
        '''
        self.record( self.camera.copy() )
        center = ( bbMin + bbMax ) * 0.5
        corners = node.bbCorners( bbMin, bbMax )
        camTrans = center - self.target
        self.target.set( center )
        self.camera.pos += camTrans
        moved = camTrans.lengthSq() > 0.0

        # transform aabb points
        corners = node.bbCorners( bbMin, bbMax )
        cornersES = map( lambda x: self.camera.eyespace( x ), corners )
        cornersES = np.array( map( lambda v: ( v.x, v.y, v.z ), cornersES ) )

        vertFOV = self.camera.fov * 0.5 * np.pi  / 180.0 # half angle in vertical direction in radians
        vertTan = np.tan( vertFOV )
        vertDepth = cornersES[ :, 2 ] - np.abs( cornersES[ :, 1] ) / vertTan
        ar = float( self.VWIDTH ) / self.VHEIGHT
        horzFOV = vertFOV * ar
        horzTan = np.tan( horzFOV )
        horzDepth = cornersES[ :, 2 ] - np.abs( cornersES[ :, 0 ] ) / horzTan
        dist = min( vertDepth.min(), horzDepth.min() )
        if ( abs( dist ) > 0.0001 ):
            moved = True
            self.camera.dolly( dist )

        if ( not moved ):
            self.popHistory()

        return moved
    

    def keyReleaseEvent( self, event, scene ):
        '''Processes a key release event.

        @param:     event       The event.
        @param:     scene       An instance of Scene -- the scene being interacted with.
        @returns:   An EventReport indicating the control's event response.
        '''
        result = ZeroWorkCamControl.keyReleaseEvent( self, event, scene )
        return result


    # VIEW HISTORY OPERATIONS
    def state( self, camera ):
        '''Returns a 2-tuple of state representing the controller and camera state.

        If a child class camera controller has data that it needs to stash, it should override this class.
        The state it returns should be a 2-tuple consiting of ( ( child class state ), parent-class state ).
        First it constructs a tuple of all the state the child class uniquely cares about.  It combines that
        into a 2-tuple with the second element being the state returned by calling the parent class's
        state method.

        @param:         camera      The camera to include in the state.
        @returns:       A tuple of state representing the minimum data to uniquely represent the camera's state.
        '''
        if ( self.downTarget is None ):
            # This is the case when I'm walking through the history
            return ( self.target.copy(), ZeroWorkCamControl.state( self, camera ) )
        else:
            # This is what happens when I'm recording the current camera
            return ( self.downTarget, ZeroWorkCamControl.state( self, camera ) )

    def setState( self, state ):
        self.target.set( state[0] )
        ZeroWorkCamControl.setState( self, state[1] )
    
    
                

