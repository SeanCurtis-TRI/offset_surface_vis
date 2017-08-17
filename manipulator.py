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
#   1. For each vertex
#       - the faces adjacent to that vertex (in counter-clockwise order) are: [f1, f2, ..., fN]
#       - for each triple (f1, f2, f3), (f2, f3, f4), ..., (fN-2, fN-1, fN), (fN-1, fN, f1), (fN, f1, f2)
#           create a vertex with the same origin and the normals as indicated
#           - place it in the list of vertices -- its index is its index in that list.
#           - enter it into a map where the key is the 3-tuple of face indices mapping to the index.
#           ** There's a gotcha here. If I do this blindly with a vertex with three adjacent faces
#               I get (f1, f2, f3), (f2, f3, f1), (f3, f1, f2) -- all the exact same planes
#               there should be only one point.
#               - simple solution is to key on # of adj faces and only do the loop of there
#                   are multiple faces.
#               - Alternative -- which might prevent future problems -- given a counter-clockwise
#                   tuple (a, b, c), it would be equally validly identified as (b, c, a) or (c, a, b).
#                   I need to create a canonical version so that as I determine three faces are
#                   intersecting, I can *know* which vertex.
#                   So, in this context, the counter-clockwise ness is irrelevant. It will be
#                   100% uniquely defined by the membership and the order is irrelevant.
#                   - so, make all keys sorted.
#   2. For each face (with index f)
#       define a clear vertex list
#       for each incident vertex (v_i)
#           Get the list of faces adjacent to v_i: [f_1, f_2, ..., f_n]
#               f must be in the list. Re-order them so that f is f1
#               For each triple: (f_1, f_2, f_3), (f_1, f_3, f_4), ..., (f_1, f_N-1, f_N)
#                   look up the index keyed by those face indices and append it to the vertex list.

# Second thoughts
#   The previous approach seems to be a good, but incomplete start.
#       It works just fine for the cube (no surprise)
#       There are facets of the gem (in certain configurations) that seem quite promising.
#       However, generally, it's crap.
#   I already knew it was incomplete -- I needed to clip things, in some sense.
#   IDEA:
#       The original mesh's vertex sets at the intersection of *multiple* planes
#       The new definition of the vertices is position based on set of deltas *and* a constraints
#           the position is based on the three planes assigned to it.
#           Constraints are the *other* planes.
#           Essentially, after computing the position, I should clip it against the *remaining*
#               planes.
#           What does this clipping look like?
#
# Icosahedron
#   I've got vertices with five adjacent faces [a, b, c, d, e]
#       I'm producing vertices for: abc, bcd, cde, dea, eab
#       However, for face a, I'm inserting indices for abc acd ade -- **acd** does not have a vertex
#           I need to not do that vertex. Yes?  No?
#       
# Numerical Issue: I'm getting horrible numerical inaccuracy in my displacements
class OffsetSurface( object ):
    '''Definition of an offset surface from a polygonal object'''
    # Given the input mesh
    #   An offset face has *at least* as many vertices as the input mesh.

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
        def __init__( self, id ):
            self.id = id
            self.vertices = []

        def __str__( self ):
            return 'F(%d) - %s' % ( self.id, self.vertices )

    class Vertex:
        '''The transform for defining the position of a vertex from displacements and normals.'''
        def __init__( self, p, n1_idx, n2_idx, n3_idx, mesh, deltas ):
            self.origin = p.copy()
            self.pos = self.origin.copy()
            self.A_inv = self._computeAInv( n1_idx, n2_idx, n3_idx, mesh )
            self.deltas = [n1_idx, n2_idx, n3_idx]
            self._updatePosition( deltas )

        def _computeAInv( self, n1_idx, n2_idx, n3_idx, mesh ):
            n1 = mesh.face_normals[:, n1_idx ]
            n2 = mesh.face_normals[:, n2_idx ]
            n3 = mesh.face_normals[:, n3_idx ]
            A = np.array( ( n1, n2, n3 ), dtype=np.float64 )
            return np.linalg.inv( A )

        def _updatePosition( self, deltas ):
            my_deltas = deltas[ self.deltas ]
            self.pos = np.dot( self.A_inv, my_deltas ) + self.origin
    
    def __init__( self, mesh ):
        '''Ctor.
        Initialize the surface from a watertight mesh instance..
        '''
        self.mesh = mesh
        self.analyze_mesh( mesh )
        self.deltas = np.zeros( (mesh.face_count(),), dtype=np.float )

        def make_key( i, j, k ):
            '''Creates a sorted tuple of the three values.'''
            values = [i, j, k]
            values.sort()
            return tuple( values )
            
        self.vertices = []      # the set of all offset vertices
        vertex_map = {}         # a map from (f_i, f_j, f_k) and the vertex at defined
                                # by the intersection of those faces.
        for i, mesh_vertex in enumerate( mesh.vertices ):
#            print mesh_vertex
            f_count = len( mesh_vertex.faces )
            p = self.mesh.vertex_pos[:3, i]

            assert( f_count > 2 )
            for f in xrange(f_count):
                f0 = mesh_vertex.faces[ f - 2 ]
                f1 = mesh_vertex.faces[ f - 1 ]
                f2 = mesh_vertex.faces[ f ]
                v_idx = len( self.vertices )
                v = self.Vertex( p, f0, f1, f2, self.mesh, self.deltas )
                self.vertices.append( v )
                key = make_key(f0, f1, f2)
                assert( not vertex_map.has_key( key ) )
                vertex_map[ key ] = v_idx
                if (f_count == 3): break    # only the single vertex

        self.faces = []
        for f_idx, mesh_face in enumerate( mesh.faces ):
#            print f, mesh_face
            face_vertices = []
            for v_idx in mesh_face.vertices:
#                print "\tv:", v_idx
                mesh_vertex = mesh.vertices[ v_idx ]
#                print "\t\t", mesh_vertex
                found_idx = mesh_vertex.faces.index( f_idx )
                source_verts = mesh_vertex.faces[found_idx:] + mesh_vertex.faces[:found_idx]
#                print "\t\tSource:", source_verts
                for i in xrange(1, len(source_verts) - 1):
                    key = make_key(f_idx, source_verts[i], source_verts[i + 1] )
                    face_vertices.append( vertex_map[ key ] )
            f = self.Face( f_idx )
            f.vertices = face_vertices
            self.faces.append( f )

    normals = property( lambda self: self.mesh.face_normals )

    def analyze_mesh( self, mesh ):
        '''Analyzes the mesh for various numerical properties'''
        # create planes for all of the faces.
        planes = np.empty( (4, mesh.face_count() ), dtype=np.float64 )
        fit_planes = np.empty( (4, mesh.face_count() ), dtype=np.float64 )
        def get_mesh_face_centroid( face, mesh ):
            '''Computes the centroid of the face on the given mesh'''
            positions = mesh.vertex_pos[ :3, face.vertices ]
            return np.sum(positions, axis=1) / len( face.vertices )
        
        def least_squares_plane( face, mesh ):
            '''Computes a plane for the face bsaed on a least-squares fit.'''
            points = mesh.vertex_pos[ :, face.vertices ].T
            zeros = np.ones( (points.shape[0], 1), dtype=np.float64 )
            x, resid, rank, s = np.linalg.lstsq( points, zeros )
            nLen = np.sqrt( np.dot( x[:3, 0], x[:3, 0] ) )
            x = ( x - np.array( ((0, 0, 0, 1),), dtype=np.float64).T ) / nLen
            return x[:, 0]

        for f_idx, face in enumerate(mesh.faces):
            centroid = get_mesh_face_centroid( face, mesh )
            fit_planes[:, f_idx] = least_squares_plane( face, mesh )
            normal = mesh.face_normals[:, f_idx]
            d = -np.dot(normal, centroid)
            planes[:3, f_idx] = normal
            planes[3, f_idx] = d

            dists = []
            for v_idx in face.vertices:
                dist = np.dot( planes[:, f_idx], mesh.vertex_pos[:, v_idx] )
                fit_dist = np.dot( mesh.vertex_pos[:, v_idx], fit_planes[:, f_idx] )
                dists.append( ( v_idx, dist, fit_dist ) )
            idx_s = ''.join( ['{0:20}'.format(d[0]) for d in dists ] )
            dist_s = ''.join( ['{0:20g}'.format(d[1]) for d in dists ] )
            fit_dist_s = ''.join( ['{0:20g}'.format(d[2]) for d in dists ] )
            print "\nFace: %d" % (f_idx)
            print '\tid\t%s' % idx_s
            print '\tdist\t%s' % dist_s
            print '\tfit\t%s' % fit_dist_s

    def get_face_centroid( self, face_index ):
        '''Computes the centroid of the given face.'''
        face = self.faces[ face_index ]
        vert_count = len( face.vertices )
        pos = self.vertices[ face.vertices[0] ].pos
        for i in xrange(1, vert_count):
            pos += self.vertices[ face.vertices[i] ].pos
        pos /= vert_count
        return pos
            
    def set_offset( self, offset, face_index ):
        '''Sets the offset value of one or all faces.
        @param  offset      The offset value. Must be a float >= 0.0.
        @param  face_index  If < 0, sets *all* faces, otherwise a valid index sets
                            the single, indexed face.
        '''
        if ( offset < 0 ): offset = 0.0
        if ( face_index < 0 ):
            self.deltas[ : ] = offset
            for v in self.vertices:
                v._updatePosition( self.deltas )
        else:
            self.deltas[ face_index ] = offset
            for v in self.faces[face_index].vertices:
                self.vertices[v]._updatePosition( self.deltas )
            
    def drawGL( self, hover_index, select ):
        '''Simply draws the mesh to the viewer'''
        class Highlighter:
            def __init__( self, hover_index, select ):
                self.hover_index = hover_index
                self.select = select
                self.colored = False
                
            def face_setup( self, f ):
                if ( self.select ):
                    glLoadName( f.id + 1 )
                elif ( f.id == self.hover_index ):
                    glColor4f( 1.0, 1.0, 0.0, 0.5 )
                    self.colored = True
                
            def face_finish( self ):
                if ( self.colored ):
                    glColor4f(1.0, 1.0, 1.0, 0.5)
                    self.colored = False

        highlighter = Highlighter( hover_index, select )

        for face in self.faces:
            highlighter.face_setup( face )
            if (len( face.vertices ) == 3 ):
                glBegin( GL_TRIANGLES )
                glNormal3fv( self.normals[:, face.id] )
                glVertex3fv( self.vertices[face.vertices[0]].pos )
                glVertex3fv( self.vertices[face.vertices[1]].pos )
                glVertex3fv( self.vertices[face.vertices[2]].pos )
                glEnd()
            elif ( len( face.vertices ) == 4 ):
                glBegin( GL_QUADS )
                glNormal3fv( self.normals[:, face.id] )
                glVertex3fv( self.vertices[face.vertices[0]].pos )
                glVertex3fv( self.vertices[face.vertices[1]].pos )
                glVertex3fv( self.vertices[face.vertices[2]].pos )
                glVertex3fv( self.vertices[face.vertices[3]].pos )
                glEnd()
            else:
                glBegin( GL_POLYGON )
                glNormal3fv( self.normals[:, face.id] )
                for i in xrange( len( face.vertices ) ):
                    glVertex3fv( self.vertices[face.vertices[i]].pos )
                glEnd()
            highlighter.face_finish()

class OffsetManipulator( SelectContext ):
    '''A manipulator for editing the offset surface.'''
    def __init__( self ):
        SelectContext.__init__( self )
        self.offset_surface = None
        self.dragging = False
        self.mouseDown = None  # screen coords of mouse at button press
        self.delta_cache = None
        self.delta_value = None

    def set_object( self, mesh_node ):
        '''Sets the underlying object that this manipulator operates on.'''
        self.offset_surface = OffsetSurface( mesh_node )

        self.hover_index = -1
        
    def clear_object( self ):
        '''Clears the underlying object'''
        self.offset_surface = None

    def draw3DGL( self, camControl, select=False ):
        '''Draws the 3D UI elements to the view.

        @param:     camControl      The scene's camera control
        @param:     select          Indicator if this draw call is made for selection purposes
        '''
        if ( self.offset_surface ):
            glPushAttrib( GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT )
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT, GL_DIFFUSE)
            glColor4f( 1, 1, 1, 0.5 )
            glLineWidth(2.0)
            
            if ( not select ):
                glDisable(GL_BLEND)
                glDisable(GL_LIGHTING)
                glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
                self.offset_surface.drawGL( self.hover_index, select )
                glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
                
            glEnable( GL_BLEND )
            glEnable(GL_LIGHTING)
            glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
            self.offset_surface.drawGL( self.hover_index, select )
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
        btns = mouse.mouseButtons()
        if (self.hover_index > -1 and btns == mouse.LEFT_BTN
            and not hasAlt and not hasCtrl):
            face_midpoint = self.offset_surface.get_face_centroid( self.hover_index )
            vec_end_point = face_midpoint + self.offset_surface.normals[:, self.hover_index]
            self.transScale, self.manipAxis = self.measureVector( Vector3( array=face_midpoint ),
                                                                  Vector3( array=vec_end_point ) )
            self.transScale = 1.0 / self.transScale
            if (hasShift):
                self.delta_cache = self.offset_surface.deltas.copy()
            else:
                self.delta_cache = np.array(
                    [self.offset_surface.deltas[self.hover_index]],
                    dtype=np.float)
            self.delta_value = self.offset_surface.deltas[self.hover_index]
            self.dragging = True
            self.mouseDown = ( event.x(), event.y() )
        return result

    def measureVector( self, p0, p1 ):
        '''Returns a 2-tuple (float, Vector2), which is the length and direction of the
        vector pointing from p0 to p1 in screen space.'''
        
        projMat = glGetDoublev( GL_PROJECTION_MATRIX )
        viewport = glGetIntegerv( GL_VIEWPORT )
        modelMat = glGetDoublev( GL_MODELVIEW_MATRIX )
        u0, v0, w0 = gluProject( p0[0], p0[1],p0[2], modelMat, projMat, viewport )
        u1, v1, w1 = gluProject( p1[0], p1[1],p1[2], modelMat, projMat, viewport )
        v = Vector2( u1 - u0, v1 - v0 )
        length = v.length()
        return length, v / length
        
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
        if (self.dragging and btn == mouse.LEFT_BTN):
            self.dragging = False
            self.mouseDown = None
        return result

    def mouseMoveEvent( self, event, camControl, scene ):
        '''Handle the mouse press event, returning an EventReport.

        @param:     event       The event.
        @param:     camControl  The scene's camera control for this event.
        @param:     scene       The scene.
        @returns:   An instance of EventReport.
        '''
        result = EventReport()
        if ( self.offset_surface ):
            hasCtrl, hasAlt, hasShift = getModState()
            if (self.dragging):
                dx = event.x() - self.mouseDown[0]
                dy = self.mouseDown[1] - event.y()
                # HORRIBLE MAGIC NUMBER!! I should really map this to screen
                # space. In other words -- at the depth of the center of this
                # face, what is the size of a pixel?
                delta_delta = (dx * self.manipAxis[0] + dy * self.manipAxis[1]) * self.transScale
                new_delta = self.delta_value + delta_delta
                new_delta = np.clip( new_delta, 0, np.infty )
                if ( not hasShift):
                    self.offset_surface.set_offset(new_delta, self.hover_index)
                else:
                    self.offset_surface.set_offset(new_delta, -1)
                result.set(True, True, False)
            else:
                new_index = -1
                # if ( not (hasCtrl or hasAlt or hasShift ) ):
                selected = self.selectSingle( None, camControl,
                                              (event.x(), event.y()) )
                if ( len( selected ) ):
                    new_index = selected.pop() - 1
                else:
                    new_index = -1
                # TODO: Only require redraw if hover_index changed
                result.set( True, new_index != self.hover_index, False )
                self.hover_index = new_index
        return result
        
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
        '''Reports the screen-space 2d vector of the given vector.

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
    
