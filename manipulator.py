from Context import *
from Select import *
from matrix import Vector3, Vector2
from XFormMatrix import BaseXformMatrix
from node import unionBB
from OpenGL.GL import *
from OpenGL.GLU import gluProject
import numpy as np
from scipy.spatial import HalfspaceIntersection, ConvexHull
import mouse
from numpy import pi, tan
import sys
import itertools

def basisFromZ(z_axis):
    '''Creates an orthonormal basis from the z_axis.

    @param z_axis   A numpy array of shape (3,). Assumed to be unit length.
                    This will serve as the z-axis (third column) of the basis.
    @returns A (3, 3) matrix.
    '''
    small_axis = np.argmin(np.abs(z_axis))
    axes = [ [1, 0, 0], [0, 1, 0], [0, 0, 1]]
    perp_axis = np.array(axes[small_axis])
    x_axis = np.cross(z_axis, perp_axis)
    x_axis /= np.sqrt(np.sum(np.dot(x_axis, x_axis)))
    y_axis = np.cross(z_axis, x_axis)
    return np.column_stack((x_axis, y_axis, z_axis))

def orderVertices(vert_idx, normal, vertex_data):
    '''Given a list of vertex indices, a plane normal, and vertex data,
    orders the indexed vertices in a counter-clockwise order.
    Assumes that all:
        1. indexed vertices are part of the convex hull.
        2. The points are all lie on a plane perpendicular to the given
            normal.

    @param  vert_idx    A list of indices in the range [0, N)
    @param  normal      An (3,) array of floats -- the normal to a plane.
    @param  vertex-data A (N, 3) array of floats -- the vertex data. One per row.
    @returns A list of indices, ordered in counter-clockwise direction (relative
    to the provided normal.
    '''
    basis = basisFromZ(normal)
    face_verts = vertex_data[vert_idx, :]  # (M, 3) matrix, vertex per row
    origin = face_verts[:1, :]
    local = face_verts - origin
    on_plane = np.dot(local, basis[:, :2])
    hull = ConvexHull(on_plane)
    return [vert_idx[i] for i in hull.vertices ]

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


    
class SimpleMesh:
    def __init__( self, vertices, faces, normals ):
        '''Constructor
        @param vertices An nx3 numpy array of vertex locations.
        @param faces a list of lists of indexes -- indices into the faces in counter clockwise order.
        @param normals: A 3XF array of normals (where there are F faces.
        '''
        self.vertices = vertices
        self.faces = faces
        self.normals = normals

    def drawGL( self ):
        for f_idx, face in enumerate( self.faces ):
            if not face: continue
            v_count = len(face)
            if ( v_count == 3 ):
                glBegin(GL_TRIANGLES)
                glNormal3fv( self.normals[:, f_idx] )
                glVertex3fv( self.vertices[ face[0], : ] )
                glVertex3fv( self.vertices[ face[1], : ] )
                glVertex3fv( self.vertices[ face[2], : ] )
                glEnd()
            elif ( v_count == 4 ):
                glBegin(GL_QUADS)
                glNormal3fv( self.normals[:, f_idx] )
                glVertex3fv( self.vertices[ face[0], : ] )
                glVertex3fv( self.vertices[ face[1], : ] )
                glVertex3fv( self.vertices[ face[2], : ] )
                glVertex3fv( self.vertices[ face[3], : ] )
                glEnd()
            else:
                glBegin(GL_POLYGON)
                glNormal3fv( self.normals[:, f_idx] )
                for v_idx in face:
                    glVertex3fv( self.vertices[ v_idx, : ] )
                glEnd()

class OffsetSurface( object ):
    '''Definition of an offset surface from a polygonal object'''
    # TODO: Document how this works.
    class Face:
        def __init__( self, id ):
            self.id = id
            self.vertices = []

        def __str__( self ):
            return 'F(%d) - %s' % ( self.id, self.vertices )
    
    def __init__( self, mesh ):
        '''Ctor.
        Initialize the surface from a watertight mesh instance..
        '''
        self.mesh = mesh
        self.hull = None
        self.deltas = np.zeros( (mesh.face_count(),), dtype=np.float )
        self.planes = np.zeros( (mesh.face_count(), 4), dtype=np.float )
        self.feasible_point = np.mean( mesh.vertex_pos, axis=1 )[:3]

        self.vertices = self.mesh.vertex_pos[:3, :].T

        # this is necessary to get an index *back* from a face for OpenGL
        # selection.
        self.faces = []
        for f_idx, mesh_face in enumerate( mesh.faces ):
            self.planes[f_idx, :3] = self.normals[:, f_idx].T
            point = self.vertices[ mesh_face.vertices[0] ]
            d = -np.dot(self.normals[:, f_idx], point)
            self.planes[f_idx, 3] = d
            
            face_vertices = []
            f = self.Face( f_idx )
            f.vertices = mesh_face.vertices
            self.faces.append( f )

    normals = property( lambda self: self.mesh.face_normals )

    def get_face_centroid( self, face_index, with_offset=False ):
        '''Computes the centroid of the given face.'''
        face = self.faces[ face_index ]
        offset = np.zeros_like(self.normals[:, face_index])
        if (with_offset):
            offset = self.normals[:, face_index] * self.deltas[face_index]
        pos = np.mean(self.vertices[face.vertices, :] + offset, axis=0)
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
        else:
            self.deltas[ face_index ] = offset
        temp_planes = self.planes.copy()
        temp_planes[:, 3] -= self.deltas
        hs = HalfspaceIntersection( temp_planes, self.feasible_point )
        verts = hs.intersections  # (N, 3) shape -- each row is a vertex
        # TODO: Due to numerical imprecision, I can end up with vertices in verts that are
        # *almost* the same (and *should* be the same. I should go through and merge them.
        # Implications:
        #   
        faces = []
        for i, f in enumerate( self.faces ):
            d = temp_planes[i, 3]   # the const for the ith plane
            n = self.normals[:, i]  # The norm for the ith plane, (3,) shape
            dist = np.dot(verts, n ) + d  # (N, 3) * (3,) -> (N,)
            indices = np.where( np.abs( dist ) < 1e-6 )[ 0 ] # (M,) matrix
            if (list(indices)):
                faces.append( orderVertices(list(indices), n, verts) )
            else:
                faces.append([])
        self.hull = SimpleMesh( verts, faces, self.normals )

    def draw_offset_face( self, face_index ):
        face = self.faces[ face_index ]
        offset = self.normals[:, face_index] * self.deltas[face_index]
        if (len( face.vertices ) == 3 ):
            glBegin( GL_TRIANGLES )
            glNormal3fv( self.normals[:, face.id] )
            glVertex3fv( self.vertices[face.vertices[0]] + offset )
            glVertex3fv( self.vertices[face.vertices[1]] + offset )
            glVertex3fv( self.vertices[face.vertices[2]] + offset )
            glEnd()
        elif ( len( face.vertices ) == 4 ):
            glBegin( GL_QUADS )
            glNormal3fv( self.normals[:, face.id] )
            glVertex3fv( self.vertices[face.vertices[0]] + offset )
            glVertex3fv( self.vertices[face.vertices[1]] + offset )
            glVertex3fv( self.vertices[face.vertices[2]] + offset )
            glVertex3fv( self.vertices[face.vertices[3]] + offset )
            glEnd()
        else:
            glBegin( GL_POLYGON )
            glNormal3fv( self.normals[:, face.id] )
            for i in xrange( len( face.vertices ) ):
                glVertex3fv( self.vertices[face.vertices[i]] + offset )
            glEnd()
            
    def draw_normal( self, hover_index ):
        if ( hover_index > -1 ):
            base = self.get_face_centroid(hover_index)
            n = self.normals[:, hover_index]
            base += n * self.deltas[ hover_index ]
            glPushAttrib(GL_COLOR_BUFFER_BIT | GL_LINE_BIT)
            glColor3f(1.0, 1.0, 0.0)
            glLineWidth(2.0)
            glBegin( GL_LINES )
            glVertex3fv(base)
            glVertex3fv(base + n )
            glEnd()
            glColor4f(1.0, 1.0, 0.0, 0.5)
            self.draw_offset_face(hover_index)
            glPopAttrib()
            
    def select_face( self ):
        '''Renders the base polygon in a way to get face selection.'''
        for f, face in enumerate(self.faces):
            glLoadName( face.id + 1 )
            self.draw_offset_face( f )
    
    def drawGL( self, hover_index, select ):
        '''Simply draws the mesh to the viewer'''
        if ( select ):
            self.select_face()
        else:
            if ( self.hull ):
                self.hull.drawGL()
            self.draw_normal( hover_index )
    
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
        self.offset_surface.set_offset(0.0, -1)
        
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
            if ( not select ):
                glDisable(GL_BLEND)
                glDisable(GL_LIGHTING)
                glDisable(GL_CULL_FACE)
                glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
                self.offset_surface.drawGL( self.hover_index, select )
                glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
                glEnable(GL_CULL_FACE)
                
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT, GL_DIFFUSE)
            glColor4f( 1, 1, 1, 0.5 )
            glLineWidth(2.0)
                
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
                selected = self.selectSingle( None, camControl,
                                              (event.x(), event.y()) )
                if ( len( selected ) ):
                    new_index = selected.pop() - 1
                else:
                    new_index = -1
                
                redraw = False
                if ( new_index != self.hover_index ):
                    redraw = True
                    self.hover_index = new_index
                result.set( True, redraw, False )
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
    
