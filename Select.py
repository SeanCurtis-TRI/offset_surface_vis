# Class for handling selection
from OpenGL.GL import *

# all registered selectable objects
SELECTABLES = [None]

# The currently selected set
GLOBAL_SELECTION = set()

# the draw state of a selectable
class SelectState:
    DRAW = 0
##    HOVER = 1
    SELECT = 2

class Selectable:
    '''Base class for selectable objects - using OpenGL selection mechanism.'''
    # The global identifiers for selectable objects.
    ID = 1
    def __init__( self ):
        '''Constructor.        '''
        self.id = Selectable.ID
        self.selected = SelectState.DRAW
        Selectable.ID += 1
        SELECTABLES.append( self )

    def glName( self ):
        '''Put the name into a gl context.'''
        glLoadName( self.id )

    def setSelected( self ):
        '''Sets the state of this node to be selected.'''
        self.selected = SelectState.SELECT

    def clearSelected( self ):
        '''Sets the state of this node to be UNselected.'''
        self.selected = SelectState.DRAW
    
BUFFER_SIZE = 1024

def addToGlobalSelection( selectSet ):
    '''Adds a selectable to the global selection set.

    @param:     selectSet       A set of selectable elements to add.
    @returns:   The number of selectables added.  Should be zero or one.
    '''
    global GLOBAL_SELECTION
    new = selectSet.difference( GLOBAL_SELECTION )
    newCount = len( new )
    if ( newCount ):
        GLOBAL_SELECTION |= new
        for item in new:
            item.setSelected()
    return newCount

def toggleGlobalSelection( selectSet ):
    '''Toggles the selectables in the given set in the global selection.

    @param:     selectSet       A set of selectables whose state should be toggled.
    @returns:   The number of selectables whose selection state is changed.
    '''
    global GLOBAL_SELECTION
    deselect = selectSet & GLOBAL_SELECTION
    select = selectSet - GLOBAL_SELECTION
    for item in deselect:
        item.clearSelected()
    for item in select:
        item.setSelected()
    GLOBAL_SELECTION |= select
    GLOBAL_SELECTION -= deselect
    return len( deselect ) + len( select )

def removeFromGlobalSelection( selectSet ):
    '''Removes the selectables in the given set from the global selection.

    @param:     selectSet       A set of selectables who should be deselected.
    @returns:   The number of selectables actually deselected.
    '''
    global GLOBAL_SELECTION
    deselect = selectSet & GLOBAL_SELECTION
    for item in deselect:
        item.clearSelected()
    GLOBAL_SELECTION -= deselect
    return len( deselect )

def setGlobalSelection( selectSet ):
    '''Removes the selectables in the given set from the global selection.

    @param:     selectSet       A set of selectables who should be deselected.
    @returns:   The number of selectables actually deselected.
    '''
    global GLOBAL_SELECTION
    deselect = GLOBAL_SELECTION - selectSet
    select = selectSet - GLOBAL_SELECTION
    for item in deselect:
        item.clearSelected()
    for item in select:
        item.setSelected()
    GLOBAL_SELECTION -= deselect
    GLOBAL_SELECTION |= select
    return len( deselect ) + len( select )

def clearGlobalSelection():
    '''Clears the selection set.'''
    count = len( GLOBAL_SELECTION )
    for s in GLOBAL_SELECTION:
        s.clearSelected()
    GLOBAL_SELECTION.clear()
    return count

def start():
    '''Starts the selection process.'''
    glSelectBuffer( BUFFER_SIZE )
    glRenderMode( GL_SELECT )
    glInitNames()
    glPushName( 0 )

def endSingle():
    '''Ends the selection process for selecting the *single* front-most element.

    @returns:       A set containing the selected element.
    '''
    hits = glRenderMode( GL_RENDER )
    # this implicitly does single selection
    selected = closestHit( hits )
    if ( selected ):
        return set( [selected] ) #{ selected }  # returning a set
    else:
        return set()
    
def endSet():
    '''Ends the selection process for selecting the *single* front-most element.

    @returns:       A set containing the selected element.
    '''
    hits = glRenderMode( GL_RENDER )
    return hitSet( hits )

def hitSet( buffer ):
    '''Produces a set of all hit records.

    @param:     buffer      The selection buffer produced by OpenGL.
    @returns:   A set consisting of all the corresponding selectables.
    '''
    return set( SELECTABLES[ record[2][0] ] for record in buffer ) #{ SELECTABLES[ record[2][0] ] for record in buffer }
    
def closestHit( buffer ):
    '''Given the ids of the elements drawn in the selection buffer,
    returns the Selectable who's depth was lowest (i.e., in front).

    @param:     buffer      The selection buffer produced by OpenGL.
    @returns:   A reference to the single closest selectable.
    '''
    closest = -1
    if ( len(buffer) == 1):
        closest = buffer[0][2][0]
    elif ( len( buffer ) > 1 ):
        closestDist = buffer[0][0]
        closest = buffer[0][2][0]
        for hit in buffer[1:]:
            testDist = hit[0]
            if ( testDist < closestDist ):
                closest = hit[2][0]
    if ( closest > -1 ):
        return SELECTABLES[ closest ]
    else:
        return None
    