# material definitions

from OpenGL.GL import *
from matrix import Vector4
from Select import SelectState

NEXT_MAT_COUNT = 0
COLORS = ( Vector4( 1.0, 0.1, 0.1, 1.0 ),
           Vector4( 1.0, 0.5, 0.1, 1.0 ),
           Vector4( 1.0, 1.0, 0.1, 1.0 ),
           Vector4( 0.5, 1.0, 0.1, 1.0 ),
           Vector4( 0.1, 1.0, 0.1, 1.0 ),
           Vector4( 0.1, 1.0, 0.5, 1.0 ),
           Vector4( 0.1, 1.0, 1.0, 1.0 ),
           Vector4( 0.1, 0.5, 1.0, 1.0 ),
           Vector4( 0.1, 0.1, 1.0, 1.0 ),
           Vector4( 0.5, 0.1, 1.0, 1.0 ),
           Vector4( 1.0, 0.1, 1.0, 1.0 ),
           Vector4( 1.0, 0.1, 0.5, 1.0 ) )
def getNextMaterial():
    '''Simple function for returning materials from a set'''
    global NEXT_MAT_COUNT
    
    mat = Material()
    mat.diffuse = COLORS[ NEXT_MAT_COUNT % len( COLORS ) ]
    NEXT_MAT_COUNT += 1
    return mat

class Material:
    SELECT_AMBIENT = Vector4( 0.95, 0.95, 0.95, 0.0 )
    def __init__( self ):
        '''Constructor.

        Defaults to a white material with no ambient.
        '''
        self.diffuse = Vector4( 1.0, 1.0, 1.0, 1.0 )
        self.ambient = Vector4( 0.0, 0.0, 0.0, 0.0 )

    def setGLHidden( self, selectState ):
        '''Sets the material's properites to an opengl context for hidden wireframe.

        @param:     selectState     The selected state of the object this
                                    material is applied to.
        '''
        if ( selectState == SelectState.DRAW ):
            glColor3f( 1.0, 1.0, 1.0 )
        elif ( selectState == SelectState.SELECT ):
            glColor3f( 0.3, 1.0, 0.3 )
            
    def setGLSolid( self, selectState ):
        '''Sets this material's properties to an opengl context.

        @param:     selectState     The selected state of the object this
                                    material is applied to.
        '''
        
        if ( selectState == SelectState.DRAW ):
            glMaterialfv( GL_FRONT, GL_DIFFUSE, self.diffuse.data )
            glMaterialfv( GL_FRONT, GL_AMBIENT, self.ambient.data )
        elif ( selectState == SelectState.SELECT ):
            glMaterialfv( GL_FRONT, GL_DIFFUSE, self.SELECT_AMBIENT.data )
            glMaterialfv( GL_FRONT, GL_AMBIENT, self.SELECT_AMBIENT.data )

    setGL = setGLSolid
    
    