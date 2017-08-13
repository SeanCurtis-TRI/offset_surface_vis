# stub for a scene graph
from matrix import *
from Context import EventReport
from Select import SelectState

class Scene( object ):
    def __init__( self ):
        # all elements to be drawn
        #   they must have a drawGL() method
        self.nodes = []
        self.sequence = None
        self._context = None

    def _setContext( self, context ):
        '''Sets the context to the scene'''
        if ( self._context ):
            self._context.deactivate()
        self._context = context
        if ( context ):
            context.activate()
            
    context = property( lambda self: self._context, lambda self, ctx: self._setContext( ctx ) )

    def clear_nodes( self ):
        '''Clears the nodes from the scene'''
        self.nodes = []
        
    # CONSTRUCTION
    def addNode( self, node ):
        '''Adds a drawable object to the scene.

        @param:     node        An instance of a scenegraph node.
        '''
        self.nodes.append( node )

    # DRAWING
    def drawGL( self, camControl, selectState=SelectState.DRAW ):
        '''Draws the scene *and* context into the current OpenGL context.

        @param:     camControl      The scene's camera control
        @param:     selectState     Indicates if the drawing is being done for
                                    selection or visualization.
        '''
        self.drawTreeGL( selectState )
        if ( self.sequence ):
            self.sequence.drawGL( selectState )
        if ( self._context ):
            self._context.drawGL( camControl )
            
    def drawTreeGL( self, selectState=SelectState.DRAW ):
        '''Draws the scene nodes in the current OpenGL context.

        @param:     selectState     Indicates if the drawing is being done for
                                    selection or visualization.
        '''
        for n in self.nodes:
            n.drawGL( selectState )

    # QUERIES
    def getBB( self ):
        '''Returns an axis-aligned bounding box on the scene.

        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        minPt = Vector3( 1e6, 1e6, 1e6 )
        maxPt = -minPt
        for n in self.nodes:
            nMin, nMax = n.getBB()
            for i in xrange( 3 ):
                if ( nMin[i] < minPt[i] ):
                    minPt[i] = nMin[i]
                if ( nMax[i] > maxPt[i] ):
                    maxPt[i] = nMax[i]
        return minPt, maxPt
    
    def center( self ):
        '''Compute the center point of the scene's geometry.

        It bounds the full scene with a bounding box and then centers on that.
        '''
        minPt, maxPt = self.getBB()
        return ( minPt + maxPt ) * 0.5

    # EVENT HANDLING
    def mousePressEvent( self, event, camControl ):
        '''Allows the scene to respond to a mouse-press event.

        @param:     event       The mouse press event.
        @param:     camControl  The scene's camera control for this event.
        @returns:   An EventReport indicating how the scene responded to the event.
        '''
        if ( self._context ):
            return self._context.mousePressEvent( event, camControl, self )
        else:
            return EventReport()
        
    def mouseReleaseEvent( self, event, camControl ):
        '''Allows the scene to respond to a mouse-release event.

        @param:     event       The mouse release event.
        @param:     camControl  The scene's camera control for this event.
        @returns:   An EventReport indicating how the scene responded to the event.
        '''
        if ( self._context ):
            return self._context.mouseReleaseEvent( event, camControl, self )
        else:
            return EventReport()
        
    def mouseMoveEvent( self, event, camControl ):
        '''Allows the scene to respond to a mouse-move event.

        @param:     event       The mouse move event.
        @param:     camControl  The scene's camera control for this event.
        @returns:   An EventReport indicating how the scene responded to the event.
        '''
        if ( self._context ):
            return self._context.mouseMoveEvent( event, camControl, self )
        else:
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
        