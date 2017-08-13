from copy import deepcopy
from struct import pack
from math import sqrt

class Face:
    def __init__( self, v=None, vn=None, vt=None ):
        if ( v == None ):
            self.verts = []
        else:
            self.verts = v
        if ( vn == None ):
            self.norms = []
        else:
            self.norms = vn
        if ( vt == None ):
            self.uvs = []
        else:
            self.uvs = vt

    def triangulate( self, vertices ):
        """Triangulates the face - returns a list of faces.

        @param:     vertices        A list of vertices.  These can be referenced to make
                                    geometrically sophisticated decisions.
        """
        if ( len( self.verts ) == 3 ):
            return [ deepcopy( self ), ]
        elif ( len( self.verts ) == 4 ):
            # convert quad to triangles
            #   Two ways to triangulate.  Pick the triangulation where the ratio of areas is
            #   as close to 1 as possible.

            # Compute two pairs of triangles: A and B
            a1 = ( vertices[ self.verts[0] - 1], vertices[ self.verts[1] - 1], vertices[ self.verts[2] - 1] )
            a2 = ( vertices[ self.verts[2] - 1], vertices[ self.verts[3] - 1], vertices[ self.verts[0] - 1] )
            b1 = ( vertices[ self.verts[0] - 1], vertices[ self.verts[1] - 1], vertices[ self.verts[3] - 1] )
            b2 = ( vertices[ self.verts[1] - 1], vertices[ self.verts[2] - 1], vertices[ self.verts[3] - 1] )
            # Compute the area of each triangle (in this case, (2 * area )^2)
            #   sufficient for the RATIO
            areaA1 = ( a1[0] - a1[1] ).cross( a1[2] - a1[1] ).lengthSq()
            areaA2 = ( a2[0] - a2[1] ).cross( a2[2] - a2[1] ).lengthSq()
            areaB1 = ( b1[0] - b1[1] ).cross( b1[2] - b1[1] ).lengthSq()
            areaB2 = ( b2[0] - b2[1] ).cross( b2[2] - b2[1] ).lengthSq()
            if ( areaA2 > areaA1 ):
                ratioA = areaA2 / areaA1
            else:
                ratioA = areaA1 / areaA2

            if ( areaB2 > areaB1 ):
                ratioB = areaB2 / areaB1
            else:
                ratioB = areaB1 / areaB2
            if ( ratioA < ratioB ):
                idx1 = ( 0, 1, 2 )
                idx2 = ( 2, 3, 0 )
            else:
                idx1 = ( 0, 1, 3 )
                idx2 = ( 1, 2, 3 )

            # nowconstruct the faces
            newFaces = []
            norms1 = norms2 = uvs1 = uvs2 = None
            verts1 = [ self.verts[ idx1[0] ], self.verts[ idx1[1] ], self.verts[ idx1[2] ] ]
            verts2 = [ self.verts[ idx2[0] ], self.verts[ idx2[1] ], self.verts[ idx2[2] ] ]
            if ( self.norms ):
                norms1 = [ self.norms[ idx1[0] ], self.norms[ idx1[1] ], self.norms[ idx1[2] ] ]
                norms2 = [ self.norms[ idx2[0] ], self.norms[ idx2[1] ], self.norms[ idx2[2] ] ]
            if ( self.uvs ):
                uvs1 = [ self.uvs[ idx1[0] ], self.uvs[ idx1[1] ], self.uvs[ idx1[2] ] ]
                uvs2 = [ self.uvs[ idx2[0] ], self.uvs[ idx2[1] ], self.uvs[ idx2[2] ] ]
            newFaces.append( Face( verts1, norms1, uvs1 ) )
            newFaces.append( Face( verts2, norms2, uvs2 ) )
            return newFaces
        else:
            newFaces = []
            # blindly create a fan triangulation (v1, v2, v3), (v1, v3, v4), (v1, v4, v5), etc...
            for i in range(1, len(self.verts) - 1):
                verts = [ self.verts[0], self.verts[i], self.verts[i+1] ]
                norms = None
                if ( self.norms ):
                    norms = [self.norms[0], self.norms[i], self.norms[i+1]]
                uvs = None
                if ( self.uvs ):
                    uvs = [self.uvs[0], self.uvs[i], self.uvs[i+1]]
                newFaces.append( Face( verts, norms, uvs ) )
            return newFaces
                

    def OBJFormat( self ):
        """Writes face definition in OBJ format"""
        s = 'f '
        vIndex = 0
        for v in self.verts:
            s += '%d' % v
            if ( self.uvs ):
                s += '/%d' % self.uvs[vIndex]
            if ( self.norms ):
                if (not self.uvs ):
                    s += '/'
                s += '/%d' % self.norms[vIndex]
            s += ' '
            vIndex += 1
        return s

    def PLYAsciiFormat( self, useNorms = False, useUvs = False ):
        """Writes face definition in PLY format"""
        s = '%d ' % (len(self.verts))
        vIndex = 0
        for v in self.verts:
            s += '%d' % ( v - 1 )
##            if ( self.uvs ):
##                s += '/%d' % self.uvs[vIndex]
##            if ( self.norms ):
##                if (not self.uvs ):
##                    s += '/'
##                s += '/%d' % self.norms[vIndex]
            s += ' '
            vIndex += 1
        return s    

    def PLYBinaryFormat( self, useNorms = False, useUvs = False ):
        """Writes face definition in PLY format"""
        s = pack('>b', len(self.verts) )
##        vIndex = 0
        for v in self.verts:
            s += pack('>i', ( v - 1 ) )
##            if ( self.uvs ):
##                s += '/%d' % self.uvs[vIndex]
##            if ( self.norms ):
##                if (not self.uvs ):
##                    s += '/'
##                s += '/%d' % self.norms[vIndex]
##            vIndex += 1
        return s            

class Vertex:
    def __init__( self, x, y, z ):
        self.pos = (x, y, z)

    def formatOBJ( self ):
        """Returns a string that represents this vertex"""
        return "v %f %f %f" % ( self.pos[0], self.pos[1], self.pos[2] )

    def asciiPlyHeader( self, count ):
        """Returns the header for this element in ply format"""
        s = 'element vertex %d\n' % ( count )
        s += 'property float x\n'
        s += 'property float y\n'
        s += 'property float z\n'
        return s
    
    def formatPLYAscii( self ):
        """Returns a string that represents this vertex in ascii ply format"""
        return "%f %f %f" % ( self.pos[0], self.pos[1], self.pos[2] )

    def binPlyHeader( self, count ):
        """Returns the header for this element in binary ply format"""
        s = 'element vertex %d\x0a' % ( count )
        s += 'property float x\x0a'
        s += 'property float y\x0a'
        s += 'property float z\x0a'
        return s

    def formatPlyBinary( self ):
        """Returns a string that represents this vertex in binary PLY format"""
        return pack('>fff', v.x, v.y, v.z)

class ColoredVertex( Vertex ):
    DEF_COLOR = ( 0, 60, 120 )
    def __init__( self, color = None ):
        Vertex.__init__( self )
        if ( color == None ):
            self.color = ColoredVertex.DEF_COLOR
        else:
            self.color = color

    def asciiPlyHeader( self, count ):
        """Returns the header for this element in ply format"""
        s = Vertex.asciiPlyHeader( self, count )
        s += 'property uchar red\n'
        s += 'property uchar green\n'
        s += 'property uchar blue\n'
        return s
    
    def formatPLYAscii( self ):
        """Returns a string that represents this vertex in ascii ply format"""
        return "%f %f %f %d %d %d" % ( self.pos[0], self.pos[1], self.pos[2],
                                       self.color[0], self.color[1], self.color[2] )

    def binPlyHeader( self, count ):
        """Returns the header for this element in binary ply format"""
        s = Vertex.binPlyHeader( self, count )
        s += 'property uchar red\x0a'
        s += 'property uchar green\x0a'
        s += 'property uchar blue\x0a'
        return s

    def formatPlyBinary( self ):
        """Returns a string that represents this vertex in binary PLY format"""
        return Vertex.formatPlyBinary( self ) + pack('>BBB', color[0], color[1], color[2])    
            
        