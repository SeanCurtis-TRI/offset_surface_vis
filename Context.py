from OpenGL.GL import *
from OpenGL.GLU import *
import Select
from mouse import *

class EventReport:
    '''Reports the results of dealing with an event'''
    def __init__( self, handled=False, visDirty=False, sceneUpdate=False ):
        # indicates that the event has been handled
        self.isHandled = handled
        # indicates that the event caused something that requires a redraw
        self.needsRedraw = visDirty
        # indicates that the event caused something that requires a scene
        #   update -- a scene update automatically implies a redraw
        self.sceneUpdate = sceneUpdate

    def __str__( self ):
        return 'EventReport: handled( %s ), redraw( %s ), update( %s )' % ( self.isHandled, self.needsRedraw, self.sceneUpdate )

    def set( self, handled, visDirty, update ):
        '''Sets both variables in a single call'''
        self.isHandled = handled
        self.needsRedraw = visDirty
        self.sceneUpdate = update

    def combine( self, report ):
        '''Combines this report with another report'''
        self.isHandled = report.isHandled or self.isHandled
        self.needsRedraw = report.needsRedraw or self.needsRedraw
        self.sceneUpdate = report.sceneUpdate or self.sceneUpdate

class Context( object ):
    '''Base class for UI contexts'''
    def __init__( self ):
        self.showHelp = False

    def activate( self ):
        '''Called when the context is activated'''
        pass

    def deactivate( self ):
        '''Called when the context is deactivated'''
        pass

    def displayHelp( self ):
        '''Displays help information for the context in the view'''
        pass

    def mousePressEvent( self, event, camControl, scene ):
        '''Handle the mouse press event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        return EventReport()

    def mouseReleaseEvent( self, event, camControl, scene ):
        '''Handle the mouse release event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        return EventReport()

    def mouseMoveEvent( self, event, camControl, scene ):
        '''Handle the mouse move event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        return EventReport()

    def keyPressEvent( self, event, camControl ):
        '''Handles key press events.

        @param:     event       The key event.
        @param:     camControl  The camera control for the view with this context.
        @returns:   An event report indicating what the contexts response to the event was.
        '''
        return EventReport()
        
    def keyReleaseEvent( self, event, camControl ):
        '''Handles key release events.

        @param:     event       The key event.
        @param:     camControl  The camera control for the view with this context.
        @returns:   An event report indicating what the contexts response to the event was.
        '''
        return EventReport()
        
    def drawGL( self, camControl ):
        '''Draw the the context's visual apparatus to the gl view'''
        if ( self.showHelp ):
            self.displayHelp()
        self.draw3DGL( camControl, Select.SelectState.DRAW )
        # set up UIGL
        glMatrixMode( GL_PROJECTION )
        glPushMatrix()
        glLoadIdentity()
        glOrtho( 0.0, camControl.VWIDTH - 1.0, 0.0, camControl.VHEIGHT - 1.0, -1.0, 1.0 )
        glMatrixMode( GL_MODELVIEW )
        glPushMatrix()
        glLoadIdentity()
        self.drawUIGL( camControl, Select.SelectState.DRAW )
        glPopMatrix()
        glMatrixMode( GL_PROJECTION )
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def setAppRunning( self, state ):
        '''The context is informed when the application is running'''
        pass

    def drawUIGL( self, camControl, select=False ):
        '''Draws the UI elements (widgets, overlays, etc.) to the view.

        @param:     camControl      The scene's camera control
        @param:     select          Indicator if this draw call is made for selection purposes
        '''
        pass

    def draw3DGL( self, camControl, select=False ):
        '''Draws the 3D UI elements to the view.

        @param:     camControl      The scene's camera control
        @param:     select          Indicator if this draw call is made for selection purposes
        '''
        pass

    def getName( self ):
        '''Returns the name of the context'''
        return self.__class__.__name__

    def initGL( self ):
        '''Gives the context a chance to initialize GL objects for a new context.'''
        pass

class SelectContext( Context ):
    '''A context which handles in scene selection'''
    def __init__( self ):
        Context.__init__( self )
        self.downPoint = None
        self.currPoint = None
        self.selecting = False

    def drawUIGL( self, camControl, select=False ):
        '''Draws the UI elements (widgets, overlays, etc.) to the view.

        @param:     camControl      The scene's camera control
        @param:     select          Indicator if this draw call is made for selection purposes
        '''
        if ( not self.currPoint is None ):
            # draw a rectangle from downPoint to currPoint
            glPushAttrib( GL_LINE_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT )
            glDisable( GL_LIGHTING )
            glLineWidth( 1.0 )
            # TODO: Translate this to screen space
            glColor3f( 0.8, 0.8, 0.8 )
            glBegin( GL_LINE_STRIP )
            glVertex3f( self.downPoint[0], self.downPoint[1], 0.0 )
            glVertex3f( self.downPoint[0], self.currPoint[1], 0.0 )
            glVertex3f( self.currPoint[0], self.currPoint[1], 0.0 )
            glVertex3f( self.currPoint[0], self.downPoint[1], 0.0 )
            glVertex3f( self.downPoint[0], self.downPoint[1], 0.0 )
            glEnd()
            glPopAttrib()
        
    def mousePressEvent( self, event, camControl, scene ):
        '''Handle the mouse press event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = EventReport()
        hasCtrl, hasAlt, hasShift = getModState()
        btn = event.button()
        if ( btn == LEFT_BTN and not hasAlt ):
            self.downPoint = ( event.x(), camControl.VHEIGHT - event.y() )
            self.selecting = True
            result.isHandled = True
        return result

    def mouseMoveEvent(  self, event, camControl, scene ):
        '''Handle the mouse move event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = EventReport()
        if ( self.selecting ):
            result.isHandled = True
            x = event.x()
            y = camControl.VHEIGHT - event.y()
            if ( x - self.downPoint[ 0 ] or y - self.downPoint[ 1 ] ):
                self.currPoint = ( x, y )
                result.needsRedraw = True
            else:
                self.currPoint = None
        return result
            
    def mouseReleaseEvent( self, event, camControl, scene ):
        '''Handle the mouse press event, returning an EventReport

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = EventReport( True )
        
        # if not handled, either perform selection or view manipulation
        hasCtrl, hasAlt, hasShift = getModState()
        btn = event.button()
        if ( btn == LEFT_BTN and not hasAlt ):
            self.selecting = False
            if ( self.currPoint is None ):
                # TODO: Eventually shift this to allow for a selection REGION
                selected = self.selectSingle( scene, camControl, ( event.x(), event.y() ) )
            else:
                selected = self.selectRegion( scene, camControl, self.downPoint, self.currPoint )
                # Need to stop drawing the selection region
                result.needsRedraw = True
                
            if ( selected ):
                if ( hasShift and hasCtrl ):
                    # add
                    result.needsRedraw |= Select.addToGlobalSelection( selected ) > 0
                elif ( hasShift ):
                    # toggle
                    result.needsRedraw |= Select.toggleGlobalSelection( selected ) > 0
                elif ( hasCtrl ):
                    # remove
                    result.needsRedraw |= Select.removeFromGlobalSelection( selected ) > 0
                else:
                    # replace
                    result.needsRedraw |= Select.setGlobalSelection( selected ) > 0
            else:
                if ( not ( hasShift or hasCtrl ) ):
                    result.needsRedraw |= Select.clearGlobalSelection() > 0
            self.currPoint = self.downPoint = None
        if ( result.needsRedraw ):
            self.selectionChanged()
        return result

    def selectSingle( self, scene, camControl, selectPoint, pickSize=5 ):
        '''Given the scene, camera and a selection point in screen space,
        performs selection and returns the single front-most selectable under the mouse.

        @param:     scene       The scene.
        @param:     camControl  The camera control.
        @param:     selectPoint The screen space point at which selection is to be done.
        @param:     pickSize        The size of the selection box around the selectPoint.
        @returns:   The selected object.
        '''
        glPushAttrib( GL_ENABLE_BIT )
        glDisable( GL_LIGHTING )
        glDisable( GL_TEXTURE_2D )

        glMatrixMode( GL_PROJECTION )
        glPushMatrix()
        glMatrixMode( GL_MODELVIEW )
        glPushMatrix()

        camControl.setSelectMat( selectPoint, pickSize )
        camControl.setGLView()

##        Select.start()
##        self.drawUIGL( Select.SelectState.SELECT )
##        selected = Select.endSingle()
        selected = None

        if ( selected is None ):
            Select.start()
            self.draw3DGL( camControl, Select.SelectState.SELECT )
            selected = Select.endSingle()
            if ( selected is None and scene is not None ):
                Select.start()
                scene.drawTreeGL( Select.SelectState.SELECT )
                selected = Select.endSingle()
        glMatrixMode( GL_PROJECTION )
        glPopMatrix()
        glMatrixMode( GL_MODELVIEW )
        glPopMatrix()
        glPopAttrib()

        return selected    
        
    def selectRegion( self, scene, camControl, point0, point1 ):
        '''Given the scene, camera and a selection *region*, returns a set of all
        selectables which intersect the region.

        @param:     scene       The scene.
        @param:     camControl  The camera control.
        @param:     point0      The x-y coordintes of one corner of the rectangular region.
        @param:     point1      The x-y coordintes of the other corner of the rectangular region.
        @returns:   The selected object.
        '''
        x0 = min( point0[0], point1[0] )
        x1 = max( point0[0], point1[0] )
        y0 = min( point0[1], point1[1] )
        y1 = max( point0[1], point1[1] )
        glPushAttrib( GL_ENABLE_BIT )
        glDisable( GL_LIGHTING )
        glDisable( GL_TEXTURE_2D )

        glMatrixMode( GL_PROJECTION )
        glPushMatrix()
        glMatrixMode( GL_MODELVIEW )
        glPushMatrix()

        camControl.setSelectMatRegion( x0, y0, x1, y1 )
        camControl.setGLView()

##        Select.start()
##        self.drawUIGL( Select.SelectState.SELECT )
##        newSelection = Select.end()
        newSelection = None

        if ( newSelection == None ):
##            Select.start()
##            self.draw3DGL( Select.SelectState.SELECT )
##            newSelection = Select.end()
            if ( newSelection == None ):
                Select.start()
                scene.drawTreeGL( Select.SelectState.SELECT )
                selected = Select.endSet()
        glMatrixMode( GL_PROJECTION )
        glPopMatrix()
        glMatrixMode( GL_MODELVIEW )
        glPopMatrix()
        glPopAttrib()

        return selected

    def selectionChanged( self ):
        '''Callback for when the selection changes'''
        pass
    
class ContextSwitcher( Context ):
    '''Class for switching between contexts through keyboard short-cuts'''
    def __init__( self ):
        Context.__init__( self )
        self.contexts = {}
        self.activeContext = None

    def addContext( self, context, key ):
        '''Add a context to the switcher, tied to a key.
        If two contexts are given the same key binding, the latter
        binding is valid.'''
        if ( self.contexts.has_key( key ) ):
            print "Old context, %s, replaced with %s" % ( self.contexts[ key ].getName(), context.getName() )
        self.contexts[ key ] = context

    def switchContexts( self, context ):
        '''Switches the active context to the given context'''
        if ( self.activeContext ):
            self.activeContext.deactivate()
        self.activeContext = context
        if ( context ):
            context.activate()

    def handleKeyboard( self, event ):
        '''Handle the keyboard event, returning an EventReport'''
        hasCtrl, hasAlt, hasShift = getModState()
        if ( not ( hasCtrl or hasAlt or hasShift ) ):
            if ( event.key == pygame.K_ESCAPE ):
                if ( self.activeContext ):
                    self.switchContexts( None )
                    return EventReport( True, True )
                if ( self.contexts.has_key( event.key ) ):
                    self.switchContexts( self.contexts[ event.key ] )
                    return EventReport( True, True )
        if ( self.activeContext ):
            return self.activeContext.handleKeyboard( event )
        return EventReport()

    def handleMouse( self, event ):
        '''Handle the mouse event, returning an EventReport'''
        if ( self.activeContext, camera, scene ):
            return self.activeContext.handleMouse( event, camera, scene )
        else:
            return EventReport()

    def drawGL( self ):
        if ( self.activeContext ):
            self.activeContext.drawGL()
        else:
            Context.drawGL( self )

    def setAppRunning( self, state ):
        '''The context is informed when the application is running'''
        for ctx in self.contexts.items():
            ctx.setAppRunning( state )

    
        