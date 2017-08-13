from Context import *
from Select import *
from matrix import Vector3, Vector2
from XFormMatrix import BaseXformMatrix
from node import unionBB
from OpenGL.GL import *
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

# TODO: Creating the offset surface
#   0. Create the following *persistent* data sets
#       a. Fx3 array of face normals (one normal per face)
#       b. Store Vx3 array of vertex positions
#       c. Store Fx1 array of offsets
#   1. In the original edge, visit each face
#   2. Walk the vertices of the face.
#       a. Find trios of faces adjacent to the vertex (always including the current face)
#       b. For that vertex store:
#           i. a slice object into the face normal array (i.e., [i, j, k] that I can use in normals[faces,:]
#           ii. Compute A^inv based on the adjacent face normals.


class OffsetSurface( object ):
    '''Definition of an offset surface from a polygonal object'''
    # Given the input mesh
    #   A offset face has *at least* as many vertices as the input mesh
    #   Strictly speaking, it has one vertex for each triple of intersecting planes
    #   For a vertex with n adjacent faces, there are n choose 3 different vertex pairings.
    #   
    #   For example, if the input mesh has a vertex with 4 incident faces,
    #       there are actually *four* coincident vertices -- one vertex for each triple
    #       of planes. So, if we enumerate the four faces 0, 1, 2, 3, we get the following
    #       triples ( 0, 1, 2 ), (0, 2, 3), (0, 1, 3), (1, 2, 3). Each produces a unique
    #       vertex which, in this configuration all happen to be coincident.
    #       The big question is, what are the definitions of these vertices and which
    #       faces use them?
    #       The position of the vertex will *always* be:
    #           p + f(A_inv, delta), where
    #               p is the original point on the rigid body
    #               A_inv is the inverse of A (where A x = delta) A is a funciton of
    #                   n_i, n_j, n_k -- the normals of the three intersecting planes
    #               delta is a vector in R3 representing the non-negative offsets of the
    #                   three intersecting planes.
    #   Hypothesis:
    #       I don't have to consider all n choose 3 combinations
    #       I only have to consider sub-sequences of the adjacency list. So, if the
    #           following faces are adjacent to vertex v (a, b, c, d, e, f), I don't
    #           have 6 choose 3 = 20 combos, I only have 6. (abc, bcd, cde, etc.)
    #           I believe this is correct due to
    #               a) The *convexity* of the geometry
    #               b) The fact that the planes are only moving outwards.
    #       This should also imply the order of the vertices
    #
    #                a_________d
    #              //
    #            / /   0
    #          / b/__________c
    #        /   /|
    #      / 1  / |    3
    #    /     / 2|
    #
    #   In the image above vertex b has four adjacent faces. That means we have four vertices:
    #       (0,1,2), (1,2,3), (2,3,0), (3,0,1) - denoted as b_0, b_1, b_2, b_3
    #       face 0 orginally had vertices: a, b, c, d
    #           Now it would have: a, b0, b2, b3, c, d
    #
    #   Everything above this is crap! It's still not right
    #   While it's true, I can define the intersecting point of three planes as an offset
    #       from the original vertex, the three plane's normals and the non-negative offset values,
    #       it is *not* true that that resulting vertex will play any roll in the final
    #       geometry.
    #       Specifically, it may get clipped by another plane in the adjacency set.
    #   It seems *highly* unlikely 
    
    class Face:
        def __init__( self ):
            pass
        
    class Vertex:
        '''A point defined by the intersection of three planes. It's final position is
        defined as an offset from a base position. The offset is a function of the
        three planes' normals and their non-negative offset values.'''
        
        def __init__( self, p_idx, n1_idx, n2_idx, n3_idx, mesh ):
            '''Constructor.
            @param  p_index     The index of the point from which this vertex derives.
            @param  n1_idx      The normal of the first plane which defines this point.
            @param  n2_idx      The normal of the second plane.
            @param  n3_idx      The normal of the third plane.
            @param  mesh        The mesh containing the normal and point position data.
            '''
            self.origin = mesh.vertices[:3, p_idx]
            self.A_inv = self._computeAInv( n1_idx, n2_idx, n3_idx, mesh )
            self.deltas = mesh.deltas[ (n1_idx, n2_idx, n3_idx) ]
            self._updatePosition()

        def _computeAInv( self, n1_idx, n2_idx, n3_idx, mesh ):
            '''The offset x from the origin of this vertex is defined by: Ax = d.
            d = [d_1, d_2, d_3] are the non-negative offset values for planes 1, 2, & 3,
                respectively.
            A is the matrix:
               | 1    n_12    n_13 |
               | n_12   1     n_23 |, where n_ij = np.dot( n_i, n_j )
               | n_13  n_23     1  |
            We're solving for x, the offset, so we need x = A^-1 d.
            '''
            n1 = mesh.normals[:, n1_idx]
            n2 = mesh.normals[:, n2_idx]
            n3 = mesh.normals[:, n3_idx]
            n_12 = np.dot( n1, n2 )
            n_13 = np.dot( n1, n3 )
            n_23 = np.dot( n2, n3 )
            A = np.array( ( (1, n_12, n_13),
                            (n_12, 1, n_23),
                            (n_13, n_23, 1) ), dtype=np.float )
            return np.linalg.inv( A )

        def _updatePosition( self ):
            '''Updates the position of this vertex based on mesh's delta values.'''
            self.pos = np.dot( self.A_inv, self.deltas )
    
                
    
    def __init__( self, mesh ):
        '''Ctor.
        Initialize the surface from a watertight mesh instance..
        '''
        self.mesh = mesh
        self.deltas = np.zeros( (mesh.face_count(),), dtype=np.float )

    vertices = property( lambda self: self.mesh.vertex_pos )
    normals = property( lambda self: self.mesh.face_normals )

    def drawGL( self ):
        '''Simply draws the mesh to the viewer'''
        pass
        
class OffsetManipulator( SelectContext ):
    '''A manipulator for editing the offset surface.'''
    def __init__( self ):
        SelectContext.__init__( self )
        self.mesh = None

    def set_object( self, mesh_node ):
        '''Sets the underlying object that this manipulator operates on.'''
        self.mesh = OffsetSurface( mesh_node )
        # TODO: Generate offset-surface data.

    def clear_object( self ):
        '''Clears the underlying object'''
        self.mesh = None
        # TODO: Clear the offset-surface data.

    def draw3DGL( self, camControl, select=False ):
        '''Draws the 3D UI elements to the view.

        @param:     camControl      The scene's camera control
        @param:     select          Indicator if this draw call is made for selection purposes
        '''
        if ( self.mesh ):
            glPushAttrib( GL_ENABLE_BIT )
            glColor3f(1.0, 1.0, 1.0)
            glDisable( GL_LIGHTING )
            glPushMatrix()
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
            self.mesh.mesh.glCommands()
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
            glPopMatrix()
            glPopAttrib()
        
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
    