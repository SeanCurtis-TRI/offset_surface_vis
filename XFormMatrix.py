from matrix import *
from math import pi, cos, sin, sqrt, atan2
from OpenGL.GL import *

DEG_TO_RAD = pi / 180.0
RAD_TO_DEG = 180.0 / pi

# rotation order
XYZ = 1
XZY = 2
YZX = 3
YXZ = 4
ZXY = 5
ZYX = 6

class Space:
    # spaces for translation
    WORLD = 1   # world
    LOCAL = 2   # local
    
    
ROT_ORDERS = {'xyz':XYZ, 'xzy':XZY, 'yzx':YZX, 'yxz':YXZ, 'zxy':ZXY, 'zyx':ZYX,
              XYZ:'xyz', XZY:'xzy', YZX:'yzx', YXZ:'yxz', ZXY:'zxy', ZYX:'zyx' }

def getEulerAngles( mat, rotOrder ):
    if ( rotOrder == XYZ ):
        i = 0; j = 1; k = 2;
        parity = 0
    elif ( rotOrder == XZY ):
        i = 0; j = 2; k = 1;
        parity = 1
    elif ( rotOrder == YXZ ):
        i = 1; j = 0; k = 2;
        parity = 1
    elif ( rotOrder == YZX ):
        i = 1; j = 2; k = 0;
        parity = 0
    elif ( rotOrder == ZXY ):
        i = 2; j = 0; k = 1;
        parity = 0
    elif ( rotOrder == ZYX ):
        i = 2; j = 1; k = 0;
        parity = 1
        
    euler = Vector3()
    cy = sqrt( mat[i][i] * mat[i][i] + mat[i][j]*mat[i][j] )
    FLT_EPSILON = 1.921e-7
    if ( cy > 16 * FLT_EPSILON ):
        euler.x = atan2( mat[j][k], mat[k][k] )
        euler.y = atan2( -mat[i][k], cy)
        euler.z = atan2( mat[i][j], mat[i][i] )
    else:
        euler.x = atan2( -mat[k][j], mat[j][j] )
        euler.y = atan2( -mat[i][k], cy )
        euler.z = 0
        
    if ( parity == 1 ):
        euler.x = -euler.x
        euler.y = -euler.y
        euler.z = -euler.z
        
    return euler

# enumerated values for determining when a matrix is valid
ALL_MAT   = 0xF # nothing is valid
ROT_MAT = 1 # rotation matrix is valid
MAT     = 2 # full matrix is valid
IMAT    = 4 # inverse matrix is valid

class BaseXformMatrix:
    '''Base transform matrix including translation, rotation and scale'''
    def __init__( self ):
        self.trans = Vector3( 0, 0, 0 )
        self.scale = Vector3( 1, 1, 1 )
        self.rot = Vector3( 0, 0, 0 )               # euler angle - in radians
        self.rotOrder = XYZ

        # cached transform matrices
        self.rotMat = Matrix4x4()
        self.rotIMat = Matrix4x4()
        self.matrix = Matrix4x4()
        self.invMatrix = Matrix4x4()
        self.clean = 0
        self.setDirty()

    def setDirty( self, valid=ALL_MAT ):
        '''Sets the full transform as dirty'''
        self.clean = self.clean & ~valid

    def setClean( self, valid=ALL_MAT ):
        self.clean = self.clean | valid

    def isClean( self, matType ):
        '''Reports if the given mat type is clean'''
        return self.clean & matType

    def __str__( self ):
        s = "BaseTransformMatrix:\n"
        s += '\tTranslation: %s\n' % ( self.trans )
        s += '\tScale: %s\n' % ( self.scale )
        s += '\tRotation: %s\n' % ( self.rot )
        return s

    def setTranslation( self, vec ):
        self.trans.set( vec )
        self.setDirty( MAT | IMAT )

    def addTranslation( self, vec ):
        self.trans += vec
        self.setDirty( MAT | IMAT )

    def setScale( self, vec ):
        self.scale.set( vec )
        self.setDirty( MAT | IMAT )
        
    def setRotationDeg( self, vec ):
        self.rot = vec * DEG_TO_RAD
        self.setDirty( ALL_MAT )

    def setRotationRad( self, vec ):
        self.rot.set( vec )
        self.setDirty( ALL_MAT )

    def addRotationDeg( self, vec ):
        self.rot += vec * DEG_TO_RAD
        self.setDirty( ALL_MAT )

    def addRotationRad( self, vec ):
        self.rot += vec
        self.setDirty( ALL_MAT )

    def translationMatrix( self, mat ):
        """Returns a 4x4 matrix for translation"""
        mat.setIdentity()
        mat.setRow( 3, self.trans.x, self.trans.y, self.trans.z, 1 )

    def translationInverseMatrix( self, mat ):
        """Returns a 4x4 matrix for inverse translation"""
        mat.setIdentity()
        mat.setRow( 3, -self.trans.x, -self.trans.y, -self.trans.z, 1 )

    def scaleMatrix( self, mat ):
        """Returns a 4x4 matrix for scale"""
        mat.setIdentity()
        mat.setDiagonal( self.scale.x, self.scale.y, self.scale.z, 1 )

    def scaleInverseMatrix( self, mat ):
        """Returns a 4x4 matrix for scale"""
        mat.setIdentity()
        mat.setDiagonal( 1.0 / self.scale.x, 1.0 / self.scale.y, 1.0 / self.scale.z, 1 )

    def rotationMatrix( self, mat ):
        """Returns a matrix for rotation"""
        if ( not self.isClean( ROT_MAT ) ):
            self.setClean( ROT_MAT )
            if ( self.rotOrder == XYZ ):
                self.xyzRotation()
            else:
                #TODO: it would POSSIBLY be more efficient if I pre-multiplied each of these matrices.  But this seems to be sufficient.
                XROT = createXRotateMatrix4( self.rot.x )
                YROT = createYRotateMatrix4( self.rot.y )
                ZROT = createZRotateMatrix4( self.rot.z )

                if ( self.rotOrder == XZY ):
                    self.rotMat.set( XROT * ZROT * YROT )
                if ( self.rotOrder == YZX ):
                    self.rotMat.set( YROT * ZROT * XROT )
                if ( self.rotOrder == YXZ ):
                    self.rotMat.set( YROT * XROT * ZROT )
                if ( self.rotOrder == ZXY ):
                    self.rotMat.set( ZROT * XROT * YROT )
                if ( self.rotOrder == ZYX ):
                    self.rotMat.set( ZROT * YROT * XROT )
            self.rotIMat.setTranspose( self.rotMat )
        mat.set( self.rotMat )

    def xyzRotation( self ):
        '''Computes the rotation matrix for xyz rotation'''
        cx = cos( self.rot.x )
        cy = cos( self.rot.y )
        cz = cos( self.rot.z )
        sx = sin( self.rot.x )
        sy = sin( self.rot.y )
        sz = sin( self.rot.z )
        self.rotMat.setRow( 0, cy*cz, cy*sz, -sy, 0 );
        self.rotMat.setRow( 1, sx*sy*cz - cx*sz, cx*cz + sx*sy*sz, sx*cy, 0 );
        self.rotMat.setRow( 2, sx*sz + cx*sy*cz, cx*sy*sz - sx*cz, cx*cy, 0 );
        self.rotMat.setRow( 3, 0, 0, 0, 1 );

    def rotationInverseMatrix( self, mat ):
        mat.set( self.rotIMat )

    def setRotationOrder( self, order ):
        if ( isinstance( order, str ) ):
            order = ROT_ORDERS[ order ]
        self.rotOrder = order

    def getTranslation( self, matrix=None):
        """Extracts the translation from a matrix as a Vector3"""
        if ( matrix == None ):
            return self.trans
        else:
            return Vector3( matrix.data[3,0], matrix.data[3,1], matrix.data[3,2] )
        
    def axisMatrix( self, origin=False ):
        """Provides the axis matrix for displaying the rotation axis.copy
        If origin is True, it displays the parent's orientation at the local translation
        If false, it displays the local rotation as well"""
        if ( origin ):
            return self.translationMatrix()
        else:
            return  self.rotationMatrix() * self.translationMatrix()

    def glRotate( self ):
        '''Perform gl rotation'''
        if ( self.rotOrder == XYZ ):
            glRotate( self.rot.z, 0, 0, 1 )
            glRotate( self.rot.y, 0, 1, 0 )
            glRotate( self.rot.x, 1, 0, 0 )
        elif ( self.rotOrder == XZY ):
            glRotate( self.rot.y, 0, 1, 0 )
            glRotate( self.rot.z, 0, 0, 1 )
            glRotate( self.rot.x, 1, 0, 0 )
        elif ( self.rotOrder == YZX ):
            glRotate( self.rot.x, 1, 0, 0 )
            glRotate( self.rot.z, 0, 0, 1 )
            glRotate( self.rot.y, 0, 1, 0 )
        elif ( self.rotOrder == YXZ ):
            glRotate( self.rot.z, 0, 0, 1 )
            glRotate( self.rot.x, 1, 0, 0 )
            glRotate( self.rot.y, 0, 1, 0 )
        elif ( self.rotOrder == ZXY ):
            glRotate( self.rot.y, 0, 1, 0 )
            glRotate( self.rot.x, 1, 0, 0 )
            glRotate( self.rot.z, 0, 0, 1 )
        elif ( self.rotOrder == ZYX ):
            glRotate( self.rot.x, 1, 0, 0 )
            glRotate( self.rot.y, 0, 1, 0 )
            glRotate( self.rot.z, 0, 0, 1 )

    def glTranslate( self ):
        '''Perform translation to the gl matris'''
        glTranslate( self.trans.x, self.trans.y, self.trans.z )
        
    def glScale( self ):
        '''Perform translation to the gl matris'''
        glScale( self.scale.x, self.scale.y, self.scale.z )
        
    def glMatrix( self ):
        '''Push the gl matrix to the gl stack'''
        glTranslate( self.trans.x, self.trans.y, self.trans.z )
        self.glRotate()
        glScale( self.scale.x, self.scale.y, self.scale.z )
        
    def getMatrix( self ):
        """Returns the Matrix4x4 representing the transformation of this transformation matrix"""
        if ( not self.isClean( MAT ) ):
            self.scaleMatrix( self.matrix )
            mat = Matrix4x4()
            self.rotationMatrix( mat )
            self.matrix.set( self.matrix * mat )
            self.translationMatrix( mat )
            self.matrix.set( self.matrix * mat )
        return self.matrix

    def cache( self ):
        '''Returns the cached data for this transform.

        @param:     A cache object for this transform -- sufficient to restore this xform
                    to its current state at some later point.
        '''
        return( self.trans.copy(), self.scale.copy(), self.rot.copy(), self.rotOrder )

    def setFromCache( self, cache ):
        '''Sets the transform matrix from the given cache object.

        @param:     cache       A cache object returned from a call to BaseXform.cache()
        '''
        t, s, r, ro = cache
        self.trans = t.copy()
        self.scale = s.copy()
        self.rot = r.copy()
        self.rotOrder = ro

        # cached transform matrices
        self.rotMat = Matrix4x4()
        self.rotIMat = Matrix4x4()
        self.matrix = Matrix4x4()
        self.invMatrix = Matrix4x4()
        self.clean = 0
        self.setDirty()
    

# TODO: Bring the extended matrix into line with the base matrix
##class TransformMatrix( BaseXformMatrix ):
##    '''Extended transform matrix including rotation pivot and rotation axis'''
##    def __init__( self ):
##        BaseXformMatrix.__init__( self )
##        self._initRotateMats()
##
##    def __str__( self ):
##        s = "TransformMatrix:\n"
##        s += '\tTranslation: %s\n' % ( self.trans )
##        s += '\tScale: %s\n' % ( self.scale )
##        s += '\tRotation: %s\n' % ( self.rot )
##        s += '\tRotate pivot: %s\n' % ( self.rotPivot )
##        s += '\tRotate axis: %s\n' % ( self.rotAxis )
##        return s
##
##    def _initRotateMats( self ):
##        """Initializes the rotate pivot, axis and pre-/post- rotation matrices"""
##        self.rotPivot = Vector3( 0, 0, 0 )
##        self.rotPivotMat = IDENTITY4x4
##        self.rotPivotIMat = IDENTITY4x4
##        
##        self.rotAxis = Vector3( 0, 0, 0 )
##        self.rotAxisMat = IDENTITY4x4
##        self.rotAxisIMat = IDENTITY4x4
##        
##        self.preRotate = IDENTITY4x4
##        self.postRotate = IDENTITY4x4
##        
##    def setRotPivot( self, pvt ):
##        self.rotPivot.set( pvt.copy )
##        self.rotPivotMat = Matrix4x4( [ [ 1, 0, 0, 0 ],
##                                        [ 0, 1, 0, 0 ],
##                                        [ 0, 0, 1, 0 ],
##                                        [ self.rotPivot.x, self.rotPivot.y, self.rotPivot.z, 1] ] )
##        self.rotPivotIMat = Matrix4x4( [ [ 1, 0, 0, 0 ],
##                                        [ 0, 1, 0, 0 ],
##                                        [ 0, 0, 1, 0 ],
##                                        [ -self.rotPivot.x, -self.rotPivot.y, -self.rotPivot.z, 1] ] )
##        try:
##            self.preRotate = self.rotPivotIMat * self.rotAxisIMat
##            self.postRotate = self.rotAxisMat * self.rotPivotMat
##        except AttributeError:
##            pass
##
##    def setRotAxisDeg( self, axis ):
##        self.rotAxis = axis * DEG_TO_RAD
##        self._updateRotAxisMat()
##
##    def setRotAxisRad( self, axis ):
##        self.rotAxis = axis.copy()
##        self._updateRotAxisMat()
##
##    def rotatePivotMatrix( self ):
##        """Returns a 4x4 matrix which represents the rotation axis (pivot and orientation)"""
##        return self.translationMatrix() * self.postRotate * self.rotationMatrix()
##    
##    def getMatrix( self ):
##        """Returns the Matrix4x4 representing the transformation of this transformation matrix"""
##        return self.xform.getMatrix()
##        R = self.rotationMatrix()
##        T = self.translationMatrix()
##        S = self.scaleMatrix()
##        return S * self.rotPivotIMat * self.rotAxisIMat * R * self.rotAxisMat * self.rotPivotMat * T
##    
##    def getInverseMatrix( self ):
##        """Returns the Matrix4x4 representing the inverse transformation of this transformation matrix"""
##        Rinv = self.rotationInverseMatrix()
##        Tinv = self.translationInverseMatrix()
##        Sinv = self.scaleInverseMatrix()
##        return Tinv * self.rotPivotIMat * self.rotAxisIMat * Rinv * self.rotAxisMat * self.rotPivotMat * Sinv        
##    
##    def glGetMatrix( self ):
##        # transation
##        glTranslatef( self.trans.x, self.trans.y, self.trans.z )
##        # revert pivot
##        glTranslatef( self.rotPivot.x, self.rotPivot.y, self.rotPivot.z )
##        # revert rotate axis
##        glRotatef( self.rotAxis.z * RAD_TO_DEG, 0, 0, 1 )
##        glRotatef( self.rotAxis.y * RAD_TO_DEG, 0, 1, 0 )
##        glRotatef( self.rotAxis.x * RAD_TO_DEG, 1, 0, 0 )
##        # perform rotation
##        glRotatef( self.rot.z * RAD_TO_DEG, 0, 0, 1 ) 
##        glRotatef( self.rot.y * RAD_TO_DEG, 0, 1, 0 )
##        glRotatef( self.rot.x * RAD_TO_DEG, 1, 0, 0 )
##        # rotate to rotate axis
##        glRotatef( -self.rotAxis.x * RAD_TO_DEG, 1, 0, 0 ) 
##        glRotatef( -self.rotAxis.y * RAD_TO_DEG, 0, 1, 0 ) 
##        glRotatef( -self.rotAxis.z * RAD_TO_DEG, 0, 0, 1 )
##        # shift by rotate pivot
##        glTranslatef( -self.rotPivot.x, -self.rotPivot.y, -self.rotPivot.z )
##        # scale
##        glScalef( self.scale.x, self.scale.y, self.scale.z )
