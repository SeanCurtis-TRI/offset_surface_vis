from geometry import Geometry, getObjGeometry
from matrix import *
from OpenGL.GL import *
# TODO: Do I need MeshEdge?

def getMeshNode( fileName, xform=None, parent=None, selectable=True ):
    '''Creates a scene graph node for an obj geometry file.

    @param:     fileName        The path to a valid obj file.
    @param:     xform           A transform matrix.  It will be the
                                identity matrix if none is provided.
    @param:     parent          Another node that serves as the
                                parent of this node.
    @returns:   An instance of a scenegraph Node containing the gometry.
    '''
    obj_geometry = getObjGeometry( fileName )
    mesh = WatertightMesh()
    mesh.from_obj( obj_geometry.objFile )
    mesh.initGL()
    is_selectable = selectable
    return mesh.instance( selectable=is_selectable )

class MeshVertex( object ):
    '''Definition of adjacency data for a mesh vertex. The interpretation
    of a MeshVertex depends on a WatertightMesh. The MeshVertex maintains *references*
    in the WatertightMesh. All vertex values (and therefore edge and face properties)
    are stored in the mesh.

    The adjacent features are stored in a "counter-clockwise" order. That is, when
    looking from the outside toward the vertex, the edges/faces are enumerated
    in counter-clockwise order such that feature[i] is adjacent to feature[i + 1].
    '''
    def __init__( self ):
        '''Constructor'''
        # indices of the faces incident to this vertex.
        self.faces = []

    def __str__( self ):
        return "V - %s" % self.faces

    def enforce_valid_order( self, mesh ):
        '''Given the mesh, confirms that the features are ordered correctly,
        changing it where necessary to enforce the counter-clockwise order.
        If re-ordering is insufficient (i.e., a feature is missing), an
        exception is thrown.'''
        face_order = self._make_adjacent_order( mesh )
        face_order = self._set_winding_order( face_order, mesh )
        self.faces = face_order

    def _make_adjacent_order( self, mesh ):
        '''Orders the faces so that each face is adjacent to the next/previous in list.
        Doesn't guarantee "winding" (i.e., counter-clockwise order).'''
        face_order = [self.faces[0]]
        remaining_faces = set(self.faces[1:])
        def is_adjacent( f_index1, f_index2 ):
            face_1 = mesh.faces[ f_index1 ]
            num_v = len( face_1.vertices )
            found = False
            face_2 = mesh.faces[ f_index2 ]
            for v, v_index in enumerate( face_1.vertices ):
                next_v = (v + 1) % num_v
                nbr_v = face_1.vertices[ next_v ]
                if ( face_2.has_edge( nbr_v, v_index ) ):
                    found = True
                    break
            return found
                
        while (remaining_faces):
            from_index = face_order[-1]
            found = False
            for nbr_index in remaining_faces:
                if ( is_adjacent( from_index, nbr_index ) ):
                    found = True
                    face_order.append( nbr_index )
                    remaining_faces.remove( nbr_index )
                    break
            if ( not found ):
                raise ValueError, "Was unable to find the next face in sequence after %d. Choices: %s" % (from_index, remaining_faces)
        if (not is_adjacent( face_order[0], face_order[-1] ) ):
            raise ValueError, "First and last faces are not adjacent"
        return face_order

    def _set_winding_order( self, adjacent_faces, mesh ):
        '''Takes a set of adjacent faces and orders them in counter-clockwise order.'''
        normals = mesh.face_normals[ :, adjacent_faces ]
        avg_norm = np.sum(normals, axis=1 )
        avg_norm /= np.sqrt( np.dot( avg_norm, avg_norm ) )
        cross = np.cross(normals[:, 0], normals[:, 1])
        if ( np.dot( cross, avg_norm ) < 0 ):
            return adjacent_faces[::-1]
        else:
            return adjacent_faces
            

class MeshFace( object ):
    '''Definition of adjacency data for a mesh vertex. The interpretation
    of a MeshFace depends on a WatertightMesh. The MeshFace maintains *references*
    in the WatertightMesh.

    The vertex order is stored in a counter-clockwise order. (Looking from
    the outside in.) A face is considerd adjacent to this face if they share
    a vertex. The adjacent face order "aligns" with the vertices. The
    0th face is adjacent to this face via the 0th vertex. However, the 1th
    face may share the 0th or 1th vertex because the vertex might have
    an arbitrarily high degree. The faces are ordered such that one can walk
    from face to face in counter-clockwise order by traversing shared edges.
    '''
    def __init__( self ):
        # Indices of the vertices that form this face.
        self.vertices = []
        # Indices of the faces adjacent to this face.
        self.faces = []

    def __str__( self ):
        return 'F(%s) - (%s)' % ( self.vertices, self.faces )

    def enforce_valid_order( self, mesh, index ):
        '''Given the mesh, confirms that the features are ordered correctly,
        changing it where necessary to enforce the counter-clockwise order.
        If re-ordering is insufficient (i.e., a feature is missing), an
        exception is thrown.

        This assumes that MeshVertex::enforce_valid_order has *already* been
        called on all of the mesh's MeshVertex instances.

        @param  mesh        The mesh containing the MeshVertex instances.
        @param  index       The index of *this* face (so it can be recognized
                            in the vertex's face adjacency list.
        '''
        # Initialization
        #   For each vertex there is an ordering of faces adjacent to that vertex.
        #   *One* of those faces is this one.
        #   Append the list (rotated as necessary) starting with the *subsequent*
        #       face and wrapping around up to, but not including this face.
        #   For each subsequent vertex
        #       Apply the previous logic, but starting with the key face as the last
        #       face in the list. (But always going up to, but not including this face).
        key_face = index
        ordered_faces = []
        for v in self.vertices:
            vert = mesh.vertices[ v ]
            f_count = len(vert.faces)
            start_idx = vert.faces.index( key_face )
            idx = ( start_idx + 1) % f_count
            while ( idx != start_idx ):
                if (vert.faces[idx] != index ):
                    ordered_faces.append( vert.faces[idx] )
                idx = (idx + 1) % f_count
            key_face = ordered_faces[-1]
            
        # The result should *always* have the first and last faces repeated
        assert( ordered_faces[0] == ordered_faces[-1] )
        self.faces = ordered_faces[:-1]

    def has_edge( self, v0, v1 ):
        '''Confirms that one of the edges of this face is formed by the
        *counter clockwise* sequence of vertices v0, v1. If they are in
        reverse order, an exception is thrown. Otherwise true is returned.
        '''
        try:
            idx = self.vertices.index( v0 )
            next_idx = (idx + 1) % len( self.vertices )
            if ( self.vertices[ next_idx ] == v1 ):
                return True
            else:
                prev_idx = idx - 1
                if ( self.vertices[ prev_idx ] == v1 ):
                    raise ValueError("The edge (%d, %d) was found reversed" % (v0, v1))
                return False
        except ValueError:
            # v0 is not in the vertex list, the edge cannot exist.
            return False


class WatertightMesh( Geometry ):
    '''A mesh with topology definition -- supporting an orderly
    set of adjacency queries.

    This requires a *watertight* mesh. That is, one that is well-defined with
    an inside and outside and no cracks or seams. In other words, every edge
    in the mesh has two and only two faces adjacent.
    '''
    def __init__( self ):
        Geometry.__init__( self )
        # A 4xV numpy array of vertex positions. They are homogeneous coordinates
        #   where self.vertex_pos[3, i] is always 1. This facilitates transform
        #   *all* the points by X * v.
        self.vertex_pos = None
        # A 3xF numpy array of face normals. This facilitates transforming normals
        #   by taking xform.rotation() * v.
        self.face_normals = None
        # A length V list of MeshVertex instances.
        self.vertices = []
        # A length F list of MeshFace instances.
        self.faces = []

    def face_count( self ):
        '''Reports the total number of faces'''
        return len( self.faces )

    def vertex_count( self ):
        '''Reports the total number of vertices'''
        return len(self.vertices)

    def getBB( self, xform=IDENTITY4x4 ):
        '''Computes the axis-aligned bounding box of this node.

        @param:         xform       The 4x4 matrix representing a particular instance
                                    of this geometry.
        @returns:       A 2-tuple of Vector3s.  The (min, max) points of the BB.
        '''
        xformed = np.dot( xform.data, self.vertex_pos )
        minPt = Vector3(array = np.min( xformed[:3, :], axis=1) )
        maxPt = Vector3(array = np.max( xformed[:3, :], axis=1) )
        return minPt, maxPt

    def from_obj( self, obj_file ):
        '''Initialize the mesh from an obj file.'''
        self._populate_from_obj( obj_file )
        self._calculateAdjacency()

    def _populate_from_obj( self, obj_file ):
        '''This populates the bare data necessary from the obj_file'''
        # initialize the vertex data.
        vert_count = len(obj_file.vertSet)
        self.vertex_pos = np.empty( ( 4, vert_count), dtype=np.float )
        self.vertex_pos[3, :] = 1.0
        self.vertices = [MeshVertex() for x in xrange(vert_count)]
        for i, v in enumerate( obj_file.vertSet ):
            self.vertex_pos[:3, i] = v.data

        # initialize face data
        grp_count, face_count = obj_file.faceStats()
        self.face_normals = np.empty( ( 3, face_count ), dtype=np.float )
        self.faces = [MeshFace() for x in xrange(face_count)]
        for i, face in enumerate( obj_file.getFaceIterator() ):
            mesh_face = self.faces[i]
            self.face_normals[:, i] = obj_file.getFaceNormal( face ).data
            # Assuming the vert index list is currently empty, copy the obj face
            #   index list into the mesh face list.
            mesh_face.vertices = [v - 1 for v in face.verts ]

    def _calculateAdjacency( self ):
        '''Given vertex positions, normals, and sets of MeshVertex and MeshFace
        instances. Computes all of the adjacency data.'''
        # Collect up the indices of all faces which use each vertex.
        f_index = range(len(self.faces))
        for i, v in enumerate(self.vertices):
            v.faces = filter( lambda f: i in self.faces[f].vertices, f_index)

        # Collect up the indices of all faces adjacent to this vertex.
        for i, f in enumerate(self.faces):
            # accumulate all of the faces that are incident to this face's vertices.
            adjacent = set()
            for v in f.vertices:
                adjacent.update( set( self.vertices[v].faces ) )
            adjacent.remove( i )
            f.faces = list( adjacent )

        # enforce invariant on feature order.
        for v in self.vertices:
            v.enforce_valid_order( self )
        for i, face in enumerate(self.faces):
            face.enforce_valid_order( self, i )
        

    def glCommands( self ):
        face_indices = range(len(self.faces))
        tris = filter( lambda face: len( self.faces[face].vertices ) == 3, face_indices )
        quads = filter( lambda face: len( self.faces[face].vertices ) == 4, face_indices )
        polys = filter( lambda face: len( self.faces[face].vertices ) > 4, face_indices )
        
        glBegin( GL_TRIANGLES )
        for f_index in tris:
            # only support per-face 
            glNormal3fv( self.face_normals[:, f_index] )
            face = self.faces[ f_index ]
            glVertex3fv( self.vertex_pos[:3, face.vertices[0]] )
            glVertex3fv( self.vertex_pos[:3, face.vertices[1]] )
            glVertex3fv( self.vertex_pos[:3, face.vertices[2]] )
        glEnd()

        glBegin( GL_QUADS )
        for f_index in quads:
            # only support per-face 
            glNormal3fv( self.face_normals[:, f_index] )
            face = self.faces[ f_index ]
            glVertex3fv( self.vertex_pos[:3, face.vertices[0]] )
            glVertex3fv( self.vertex_pos[:3, face.vertices[1]] )
            glVertex3fv( self.vertex_pos[:3, face.vertices[2]] )
            glVertex3fv( self.vertex_pos[:3, face.vertices[3]] )
        glEnd()
        
        for f_index in polys:
            glBegin( GL_POLYGON )
            # only support per-face 
            glNormal3fv( self.face_normals[:, f_index] )
            face = self.faces[ f_index ]
            for i in xrange( len( face.vertices ) ):
                glVertex3fv( self.vertex_pos[:3, face.vertices[i]] )
            glEnd()
            
if __name__ == '__main__':    
    from ObjReader import ObjFile
    mesh = WatertightMesh()
    mesh.from_obj( ObjFile( 'facet.obj' ) )
    print "Bounding box", mesh.getBB()