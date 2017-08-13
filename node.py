# Stubs for a scenegraph

from OpenGL.GL import *
from matrix import *
from material import *
from Select import Selectable, SelectState
from XFormMatrix import *

# NOTE:
#   I've mushed three concepts together
#       1) A generic graph node
#       2) A DagNode
#       3) Transform
#   Generic graph nodes are simply the minimum primitive for existing in the graph
#   The DagNode is one that can take children.
#   The Transform is a DagNode that has a transformation.
#
#   If these were unique, a geometry node would simply be a node.
#       positioning it in space would require placing a transform Node above it.  (a la Maya)
#   In this light, every node has a transform.

def unionBB( min0, max0, min1, max1 ):
    '''Creates a bounding box which bounds both bounding boxes.

    @param:     min0        The minimum point of the first bounding box.
    @param:     min1        The maximum point of the first bounding box.
    @param:     min0        The minimum point of the first bounding box.
    @param:     min1        The maximum point of the first bounding box.
    @returns:   Two 2-tuples of floats.  The minimum and maximum points of the
                overall bounding box.
    '''
    minPt = min0.copy()
    maxPt = max0.copy()
    for i in xrange( 3 ):
        if ( min1[i] < minPt[i] ):
            minPt[i] = min1[i]
        if ( max1[i] > maxPt[i] ):
            maxPt[i] = max1[i]
    return minPt,maxPt

def bbCorners( minPt, maxPt ):
    '''Given the minimum and maximum points of a bounding box, prodcues a list of vectors
    containing all points on the bounding box.

    @returns:        A list of 8 Vector3 instances.  The 8 points of the bounding box.
    '''
    return [ minPt,
             maxPt,
             Vector3( minPt.x, minPt.y, maxPt.z ),
             Vector3( minPt.x, maxPt.y, maxPt.z ),
             Vector3( minPt.x, maxPt.y, minPt.z ),
             Vector3( maxPt.x, maxPt.y, maxPt.z ),
             Vector3( maxPt.x, minPt.y, maxPt.z ),
             Vector3( maxPt.x, maxPt.y, minPt.z )
             ]
             

class Node( object ):
    '''Basic node in the scene graph.
    It includes a transform and the ability to have children.
    '''
    def __init__( self, xform=IDENTITY4x4, parent=None ):
        '''Constructor.

        @param:     drawable        The drawable associated with this node.
        '''
        self.xform = BaseXformMatrix()
        self.visible = True
        self.children = []
        self._parent = parent
        if ( parent ):
            parent.children.append( self )
        self.cleared = False
        self.clearMatrices()

    def _setParent( self, parent ):
        '''Sets the parent of this node.'''
        if ( self._parent != parent ):
            # remove from previous parent
            if ( self._parent ):
                self._parent.removeChild( self )
            # add to new parent
            if ( parent ):
                parent.addChild( self )

    parent = property( lambda self: self._parent, lambda self, p: self._setParent( p ) )

    def clearMatrices( self ):
        """Clears all of the cached matrices: local, parent and world"""
        if ( not self.cleared ):
            self.matrix = None
            self.invMatrix = None
            self.worldMatrix = None
            self.worldInverseMatrix = None
            self.parentMatrix = None
            self.parentInverseMatrix = None
            for child in self.children:
                child.clearMatrices()
            self.cleared = True
      
    def setTranslation( self, vec ):
        self.xform.setTranslation( vec )
        self.clearMatrices()

    def addTranslation( self, vec ):
        self.xform.addTranslation( vec )
        self.clearMatrices()
        
    def setScale( self, vec ):
        self.xform.setScale( vec )
        self.clearMatrices()

    def setRotationDeg( self, vec ):
        self.xform.setRotationDeg( vec )
        self.clearMatrices()

    def setRotationRad( self, vec ):
        self.xform.setRotationRad( vec )
        self.clearMatrices()

    def addRotationDeg( self, vec ):
        self.xform.addRotationDeg( vec )
        self.clearMatrices()

    def addRotationRad( self, vec ):
        self.xform.addRotationRad( vec )
        self.clearMatrices()

    def setRotationOrder( self, order ):
        self.xform.setRotationOrder( order )
        self.clearMatrices()
        
    def getMatrix( self ):
        """Returns the local transformation matrix"""
        if ( not self.matrix ):
            self.matrix = self.xform.getMatrix()
            self.cleared = False
        return self.matrix

    def getInverseMatrix( self ):
        """Returns the local inverse transformation matrix"""
        if ( not self.invMatrix ):
            self.invMatrix = self.xform.getInverseMatrix()
            self.cleared = False
        return self.invMatrix

    def getWorldMatrix( self ):
        """Returns the matrix which transforms this space to the world space"""
        if ( not self.worldMatrix ):
            if ( self.parent ):
                self.worldMatrix = self.getMatrix() * self.parent.getWorldMatrix()
            else:
                self.worldMatrix = self.getMatrix()
            self.cleared = False
        return self.worldMatrix

    def getWorldInverseMatrix( self ):
        """Returns the matrix which transforms world coordiantes into this space"""
        if ( not self.worldInverseMatrix ):
            if ( self.parent ):
                self.worldInverseMatrix = self.parent.getWorldInverseMatrix() * self.getInverseMatrix()
            else:
                self.worldInverseMatrix = self.getInverseMatrix().copy()
            self.cleared = False
        return self.worldInverseMatrix
    
    def getParentMatrix( self ):
        """Returns the parent's world matrix"""
        if ( not self.parentMatrix ):
            if ( self.parent ):
                self.parentMatrix = self.parent.getWorldMatrix()
            else:
                self.parentMatrix = IDENTITY4x4
            self.cleared = False
        return self.parentMatrix

    def getParentInverseMatrix( self ):
        """Returns the parent's world inverse matrix"""
        if ( not self.parentInverseMatrix ):
            self.parentMatrix = self.parent.getWorldInverseMatrix()
            self.cleared = False
        return self.parentMatrix

    # query portions of the transformation matrix
    def getTranslation( self, space=Space.WORLD ):
        """Returns the translation value of this transform node -- either in world or local space"""
        # returns a Vector3
        if ( space == Space.WORLD ):
            return self.xform.getTranslation( self.getWorldMatrix() )
        elif ( space == Space.LOCAL ):
            return self.xform.trans
        
    def drawGL( self, selectState=SelectState.DRAW, forceVisible=False ):
        '''Draws this node to the current OpenGL context.

        @param:     selectState     Indicates if the drawing is being done for
                                    selection or visualization.
        '''
        if ( self.visible or forceVisible ):
            glPushMatrix()
            mat = self.xform.getMatrix()
            glMultMatrixf( mat.getFlattened() )
            self.drawCommands( selectState )
            
            for child in self.children:
                child.drawGL( selectState )
            glPopMatrix()
##        self.drawBB()

    def drawCommands( self, selectState ):
        '''The draw commands for this actual node's contents'''
        pass

    def getBB( self ):
        '''Computes the axis-aligned bounding box of this node.

        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        minPt = Vector3( 1e6, 1e6, 1e6 )
        maxPt = -minPt
        for n in self.children:
            nMin, nMax = n.getBB()
            minPt, maxPt = unionBB( minPt, maxPt, nMin, nMax )
        return minPt, maxPt

    def drawBB( self ):
        '''Draws the bounding box on this node.'''
        minPt, maxPt = self.getBB()
        glPushAttrib( GL_COLOR_BUFFER_BIT | GL_LINE_BIT | GL_ENABLE_BIT )
        glDisable( GL_LIGHTING )
        glColor3f( 0.2, 0.9, 0.9 )
        glLineWidth( 2.0 )
        glBegin( GL_LINE_STRIP )
        glVertex3f( minPt[0], minPt[1], minPt[2] )
        glVertex3f( maxPt[0], minPt[1], minPt[2] )
        glVertex3f( maxPt[0], maxPt[1], minPt[2] )
        glVertex3f( minPt[0], maxPt[1], minPt[2] )
        glVertex3f( minPt[0], minPt[1], minPt[2] )
        glVertex3f( minPt[0], minPt[1], maxPt[2] )
        glVertex3f( maxPt[0], minPt[1], maxPt[2] )
        glVertex3f( maxPt[0], maxPt[1], maxPt[2] )
        glVertex3f( minPt[0], maxPt[1], maxPt[2] )
        glVertex3f( minPt[0], minPt[1], maxPt[2] )
        glEnd()
        glBegin( GL_LINES )
        glVertex3f( minPt[0], maxPt[1], minPt[2] )
        glVertex3f( minPt[0], maxPt[1], maxPt[2] )
        glVertex3f( maxPt[0], maxPt[1], minPt[2] )
        glVertex3f( maxPt[0], maxPt[1], maxPt[2] )
        glVertex3f( maxPt[0], minPt[1], minPt[2] )
        glVertex3f( maxPt[0], minPt[1], maxPt[2] )
        glEnd()
        glPopAttrib()
        
class DrawableNode( Node ):
    '''A scenegraph node which actually has something to draw'''
    def __init__( self, drawable, xform=IDENTITY4x4, parent=None ):
        Node.__init__( self, xform, parent )
        self.drawable = drawable

    def getBB( self ):
        '''Computes the axis-aligned bounding box of this node.

        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        minPt, maxPt = self.drawable.getBB( self.getWorldMatrix() )
        childMin, childMax = Node.getBB( self )
        return unionBB( minPt, maxPt, childMin, childMax )

    def drawCommands( self, selectState ):
        self.drawable.drawGL()        
        
class GeoNode( DrawableNode ):
    '''A scenegraph node which draws geometry with materials'''
    def __init__( self, drawable, xform=IDENTITY4x4, parent=None ):
        DrawableNode.__init__( self, drawable, xform, parent )
        self.material = Material()

    def drawCommands( self, selectState ):
        self.material.setGL( selectState )
        DrawableNode.drawCommands( self, selectState )

    def setMaterial( self, material ):
        '''Sets the node's material.

        @param:     material        The material to use for this node.
        '''
        self.material = material        

class SelectableGeoNode( GeoNode, Selectable ):
    '''A scene graph node for a selectable geometry node'''
    def __init__( self, drawable, xform=IDENTITY4x4, parent=None ):
        GeoNode.__init__( self, drawable, xform, parent )
        Selectable.__init__( self )


    def drawCommands( self, selectState=SelectState.DRAW ):
        '''Draws the node into the current OpenGL context.

        @param:     selectState     Indicates if the drawing is being done for
                                    selection or visualization.
        '''
        if ( selectState == SelectState.SELECT ):
            self.glName()
            self.drawable.drawGL( selectState )
        else:
            self.material.setGL( self.selected )
            self.drawable.drawGL( selectState )