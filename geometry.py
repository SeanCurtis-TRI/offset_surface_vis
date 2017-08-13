# defines geometry for drawing in a context
from OpenGL.GL import *
from node import SelectableGeoNode, GeoNode
from matrix import *
from ObjReader import ObjFile
from material import getNextMaterial
from Select import SelectState

OBJS = {}

def getObjGeometry( fileName ):
    '''Creates a geometric drawable from a obj file.

    @param:     fileName        The path to a valid obj file.
    @returns:   An instance of a Geometry drawable.
    '''
    if ( fileName in OBJS ):
        return OBJS[ fileName ]
    obj = ObjGeometry( ObjFile( fileName ) )
    OBJS[ fileName ] = obj
    return obj

def getObjNode( fileName, xform=None, parent=None, selectable=True ):
    '''Creates a scene graph node for an obj geometry file.

    @param:     fileName        The path to a valid obj file.
    @param:     xform           A transform matrix.  It will be the
                                identity matrix if none is provided.
    @param:     parent          Another node that serves as the
                                parent of this node.
    @returns:   An instance of a scenegraph Node containing the gometry.
    '''
    geom = getObjGeometry( fileName )
    is_selectable = selectable
    return geom.instance( selectable=is_selectable )

class Geometry:
    '''A drawable geometry element'''
    def __init__( self ):
        '''Constructor'''
        # the open gl id
        self.GL_ID = 0

    def initGL( self ):
        '''Initializes the display list for the geometry'''
        self.GL_ID = glGenLists( 1 )
        glNewList( self.GL_ID, GL_COMPILE )
        self.glCommands()
        glEndList()
        
    def drawGL( self, selectState=SelectState.DRAW ):
        glPushAttrib( GL_ENABLE_BIT )
        if ( selectState == SelectState.SELECT ):
            glDisable( GL_LIGHTING )
            
        glCallList( self.GL_ID )
        glPopAttrib()

    def instance( self, xform=None, parent=None, selectable=True ):
        '''Create an instance of the geometry with the (optionally)
        provided parent and transform.

        @param:     xform       A transform matrix.  It will be the
                                identity matrix if none is provided.
        @param:     parent      Another node that serves as the
                                parent of this node.
        '''
        if ( selectable ):
            node = SelectableGeoNode( self, xform, parent )
        else:
            node = GeoNode( self, xform, parent )
        node.setMaterial( getNextMaterial() )
        return node

    def getBB( self, xform=IDENTITY4x4 ):
        '''Computes the axis-aligned bounding box of this node.

        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        return Vector3( 1e6, 1e6, 1e6 ), Vector3( -1e6, -1e6, -1e6 )

class TestCube( Geometry ):
    '''A simple cube'''
    SIZE = 0.5

    def __init__( self ):
        Geometry.__init__( self )
        self.initGL()
        
    def glCommands( self ):
        # front
        glColor3f( 1.0, .1, .1 )
        glBegin( GL_QUADS )
        glNormal3f( 0, 0, -1 )
        glVertex3f( -self.SIZE, -self.SIZE, -self.SIZE )
        glVertex3f( -self.SIZE, self.SIZE, -self.SIZE )
        glVertex3f( self.SIZE, self.SIZE, -self.SIZE )
        glVertex3f( self.SIZE, -self.SIZE, -self.SIZE )

        # back
        glColor3f( .1, 1., 0.1 )
        glNormal3f( 0, 0, 1 )
        glVertex3f( -self.SIZE, -self.SIZE, self.SIZE )
        glVertex3f( self.SIZE, -self.SIZE, self.SIZE )
        glVertex3f( self.SIZE, self.SIZE, self.SIZE )
        glVertex3f( -self.SIZE, self.SIZE, self.SIZE )

        # top
        glColor3f( 0.9, 0.9, 0.9 )
        glNormal3f( 0, 1, 0 )
        glVertex3f( -self.SIZE, self.SIZE, -self.SIZE )
        glVertex3f( -self.SIZE, self.SIZE, self.SIZE )
        glVertex3f( self.SIZE, self.SIZE, self.SIZE )
        glVertex3f( self.SIZE, self.SIZE, -self.SIZE )

        # bottom
        glColor3f( 0.1, 0.1, 0.1 )
        glNormal3f( 0, -1, 0 )
        glVertex3f( -self.SIZE, -self.SIZE, -self.SIZE )
        glVertex3f( self.SIZE, -self.SIZE,- self.SIZE )
        glVertex3f( self.SIZE, -self.SIZE, self.SIZE )
        glVertex3f( -self.SIZE, -self.SIZE, self.SIZE )

        # right
        glColor3f( 0.1, 0.1, 1.0 )
        glNormal3f( 1, 0, 0 )
        glVertex3f( self.SIZE, -self.SIZE, self.SIZE )
        glVertex3f( self.SIZE, -self.SIZE, -self.SIZE )
        glVertex3f( self.SIZE, self.SIZE, -self.SIZE )
        glVertex3f( self.SIZE, self.SIZE, self.SIZE )

        # right
        glColor3f( 0.9, 0.5, 0.1 )
        glNormal3f( -1, 0, 0 )
        glVertex3f( -self.SIZE, -self.SIZE, self.SIZE )
        glVertex3f( -self.SIZE, self.SIZE, self.SIZE )
        glVertex3f( -self.SIZE, self.SIZE, -self.SIZE )
        glVertex3f( -self.SIZE, -self.SIZE, -self.SIZE )
        glEnd()

    def getBB( self, xform=IDENTITY4x4 ):
        '''Computes the axis-aligned bounding box of this node.

        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        pts = (
            Vector3( -self.SIZE, -self.SIZE, -self.SIZE ),
            Vector3( self.SIZE, -self.SIZE, -self.SIZE ),
            Vector3( self.SIZE, -self.SIZE, self.SIZE ),
            Vector3( -self.SIZE, -self.SIZE, self.SIZE ),
            Vector3( -self.SIZE, self.SIZE, -self.SIZE ),
            Vector3( self.SIZE, self.SIZE, -self.SIZE ),
            Vector3( self.SIZE, self.SIZE, self.SIZE ),
            Vector3( -self.SIZE, self.SIZE, self.SIZE )
            )
        minPt = Vector3( 1e6, 1e6, 1e6 )
        maxPt = -minPt
        for pt in pts:
            v = pt * xform 
            for i in xrange( 3 ):
                if ( v[i] < minPt[i] ):
                    minPt[i] = v[i]
                if ( v[i] > maxPt[i] ):
                    maxPt[i] = v[i]
        return minPt, maxPt

class ObjGeometry( Geometry ):
    '''A drawable geometry element based on an obj file'''
    def __init__( self, objFile ):
        Geometry.__init__( self )
        self.objFile = objFile
        self.initGL()

    def glCommands ( self ):
        verts = self.objFile.vertSet
        norms = self.objFile.normSet
        tris = filter( lambda x: len( x.verts ) == 3, self.objFile.getFaceIterator() )
        quads = filter( lambda x: len( x.verts ) == 4, self.objFile.getFaceIterator() )
        polys = filter( lambda x: len( x.verts ) > 4, self.objFile.getFaceIterator() )
        
        if ( norms ):
            glBegin( GL_TRIANGLES )
            for tri in tris:
                v = verts[ tri.verts[ 0 ] - 1 ]
                n = norms[ tri.norms[ 0 ] - 1 ]
                glNormal3f( n.x, n.y, n.z )
                glVertex3f( v.x, v.y, v.z )
                v = verts[ tri.verts[ 1 ] - 1 ]
                n = norms[ tri.norms[ 1 ] - 1 ]
                glNormal3f( n.x, n.y, n.z )
                glVertex3f( v.x, v.y, v.z )
                v = verts[ tri.verts[ 2 ] - 1 ]
                n = norms[ tri.norms[ 2 ] - 1 ]
                glNormal3f( n.x, n.y, n.z )
                glVertex3f( v.x, v.y, v.z )
            glEnd()

            glBegin( GL_QUADS )
            for quad in quads:
                for i in xrange( 4 ):
                    v = verts[ quad.verts[ i ] - 1 ]
                    n = norms[ quad.norms[ i ] - 1 ]
                    glNormal3f( n.x, n.y, n.z )
                    glVertex3f( v.x, v.y, v.z )
            glEnd()
            
            for poly in polys:
                glBegin( GL_POLYGON )
                for i in xrange( len( poly.verts ) ):
                    v = verts[ poly.verts[ i ] - 1 ]
                    n = norms[ poly.norms[ i ] - 1 ]
                    glNormal3f( n.x, n.y, n.z )
                    glVertex3f( v.x, v.y, v.z )
                glEnd()
        else:
            glBegin( GL_TRIANGLES )
            for tri in tris:
                v1 = verts[ tri.verts[ 0 ] - 1 ]
                v2 = verts[ tri.verts[ 1 ] - 1 ]
                v3 = verts[ tri.verts[ 2 ] - 1 ]
                n = ( v3 - v2 ).cross( v1 - v2 ).normalize()
                glNormal3f( n.x, n.y, n.z )
                glVertex3f( v1.x, v1.y, v1.z )
                glVertex3f( v2.x, v2.y, v2.z )
                glVertex3f( v3.x, v3.y, v3.z )
            glEnd()

            glBegin( GL_QUADS )
            for quad in quads:
                v1 = verts[ quad.verts[ 0 ] - 1 ]
                v2 = verts[ quad.verts[ 1 ] - 1 ]
                v3 = verts[ quad.verts[ 2 ] - 1 ]
                v4 = verts[ quad.verts[ 3 ] - 1 ]
                n = ( v1 - v2 ).cross( v3 - v2 ).normalize()
                glNormal3f( -n.x, -n.y, -n.z )
                glVertex3f( v1.x, v1.y, v1.z )
                glVertex3f( v2.x, v2.y, v2.z )
                glVertex3f( v3.x, v3.y, v3.z )
                glVertex3f( v4.x, v4.y, v4.z )
            glEnd()
            
            for poly in polys:
                glBegin( GL_POLYGON )
                v1 = verts[ poly.verts[ 0 ] - 1 ]
                v2 = verts[ poly.verts[ 1 ] - 1 ]
                v3 = verts[ poly.verts[ 2 ] - 1 ]
                v4 = verts[ poly.verts[ 3 ] - 1 ]
                n = ( v4 - v2 ).cross( v1 - v2 ).normalize()
                glNormal3f( n.x, n.y, n.z )
                glVertex3f( v1.x, v1.y, v1.z )
                glVertex3f( v2.x, v2.y, v2.z )
                glVertex3f( v3.x, v3.y, v3.z )
                glVertex3f( v4.x, v4.y, v4.z )
                for i in xrange( 4, len( poly.verts ) ):
                    v = verts[ poly.verts[ i ] - 1 ]
                    glVertex3f( v[0], v[1], v[2] )
                glEnd()

    def getBB( self, xform=IDENTITY4x4 ):
        '''Computes the axis-aligned bounding box of this node.

        @param:         xform       The 4x4 matrix representing a particular instance
                                    of this geometry.
        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        return self.objFile.getBB( xform )

            
        