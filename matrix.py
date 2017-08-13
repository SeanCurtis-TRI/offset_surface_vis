#from math import sqrt, cos, sin, pi
import numpy as np
ANGTORAD = np.pi / 180.0

##class Matrix:
##    def canMultiply( self, object ):
##        return False

FLOAT = np.float32  # np.float64
EPS = 1e-5
PRINT_RESOLUTION = 3

class Vector( object ):
    '''A basic class for representing vectors of arbitrary length.'''

    # DATA MANIPULATION
    def __getitem__( self, index ):
        '''Access an element of the vector through a zero-valued index.

        The function assumes the the index is valid.  If the index proves to be
        invalid, an IndexError is raised.
        
        @param:     index       The index of the element.
        '''
        return self.data[ index ]

    def __setitem__( self, index, value ):
        '''Set an element of the vector through a zero-valued index.

        The function assumes the the index is valid.  If the index proves to be
        invalid, an IndexError is raised.
        
        @param:     index       The index of the element.
        @param:     value       The value to set in the vector at the index.
        '''
        self.data[ index ] = value     

    def set( self, v ):
        '''Sets the values of this object with the given values in v.

        @param:     v       An object which can be interpreted as a vector.
                            Either an instance of this vector, or a tuple of appropriate length.
        '''
        # this assumes that v's data is the same size as this.
        if ( isinstance( v, self.__class__ ) ):
            self.data[:] = v.data
        else:
            # assume it is a tuple of appropriate length
            self.data[:] = v

    def asTuple( self ):
        '''Returns a tuple version of the vector.

        @returns:   A n-tuple, where the vector has n elements.
        '''
        return tuple( self.data.tolist() ) 

    def getList( self ):
        '''Returns a list version of the vector.

        Changing the elements of the list will *not* change the elements of the vector.

        @returns:   A list of n floats, where the vector has n elements.
        '''
        return self.data.tolist()

    # MATHEMATICAL OPERATIONS
    def __neg__( self ):
        '''Vector negation.

        @returns:       A new vector with all elements negated.
        '''
        return self.__class__( array = -self.data )
    
    def __add__( self, v ):
        '''Vector addition - element-wise addition.

        @param:     v       The vector to add to this one.
        @returns:   A new vector containing the element-wise addition.
        '''
        assert( v.__class__ == self.__class__ )
        return self.__class__( array = self.data + v.data )

    def __iadd__( self, v ):
        '''In-place vector addition - element-wise addition.

        @param:     v       The vector to add to this one.
        @returns:   A reference to this vector.
        '''
        assert( v.__class__ == self.__class__ )
        self.data += v.data
        return self

    def __sub__( self, v ):
        '''Vector subtraction - element-wise subtration.

        @param:     v       The vector to subtract from this one.
        @returns:   A new vector containing the element-wise subtraction.
        '''
        assert( v.__class__ == self.__class__ )
        return self.__class__( array = self.data - v.data )
    
    def __isub__( self, v ):
        '''In-place vector subtraction - element-wise subtration.

        @param:     v       The vector to subtract from this one.
        @returns:   A reference to this vector.
        '''
        assert( v.__class__ == self.__class__ )
        self.data -= v.data
        return self

    def __mul__(self, m ):
        '''Multiplies this vector on the right by the given multiplicand.

        The multiplicand can be a scalar or a vector of the same size.

        @param:     m       The multiplicand.
        @returns:   A new vector instance.  If m is a scalar, then it contains the scaled values of
                    this vector.  If m is a vector of the same size, the new vector contains they
                    element-wise products of the two vectors.
        '''
        if ( isinstance( m, float ) or isinstance( m, int ) or isinstance( m, np.floating ) or isinstance( m, np.integer ) ):
            return self.__class__( array = self.data * m )
        elif ( isinstance( m, self.__class__ ) ):
            return self.__class__( array = self.data * m.data )
        else:
            raise ValueError, "Can't multiply object of type %s against a %s" % ( m.__class__.__name__, self.__class__.__name__ )

    def __rmul__(self, m ):
        '''Multiplies this vector on the left by a scalar multiplicand, m.

        @param:     m       The scalar multiplicand.
        @returns:   A new vector instance.
        @raises:    ValueError if the multiplicand is not a scalar.
        '''
        if ( isinstance( m, float ) or isinstance( m, int ) or isinstance( m, np.floating ) or isinstance( m, np.integer ) ):
            return self.__class__( array = self.data * m )
        else:
            raise ValueError, "Can't multiply object of type %s against a %s" % ( m.__class__.__name__, self.__class__.__name__ )

    def __imul__( self, m ):
        '''In-place multiplication by a scalar.

        @param:     m       The scalar multiplicand.
        @returns:   A reference to this vector.
        '''
        assert( isinstance( m, float ) or isinstance( m, int ) or isinstance( m, np.floating ) or isinstance( m, np.integer ) )
        self.data *= m
        return self

    def __div__( self, s ):
        '''Element-wise division by a scalar.

        @param:     s       The scalar divisor.
        @returns:   A new vector with each element divided by the scalar.
        '''
        recip = 1.0 / s
        return self * recip

    # VECTOR OPERATIONS
    def length( self ):
        '''Computes the magnitude of this vector.

        @returns:   A float scalar.  The length of the vector.
        '''
        return np.sqrt( np.dot( self.data, self.data ) )

    def lengthSq( self ):
        '''Computes the squared magnitude of this vector.

        @returns:   A float scalar.  The squared length of the vector.
        '''
        return np.dot( self.data, self.data )

    def normalize( self ):
        '''Returns a normalized vector in the same direction as this vector.

        If the original vector has no length (i.e. the zero vector), the resultant vector will
        likewise have zero length.

        @returns:   A new Vector3.
        '''
        len = self.length()
        if ( len < EPS ):
            return self.__class__()
        else:
            invLen = 1.0 / len
            return self.__class__( array = self.data * invLen )            

    def normalize_ip( self ):
        """Normalized the vector in place so that the length equals one"""
        len = self.length()
        if ( len < EPS ):
            self.data[:] = 0.0
        else:
            invLen = 1.0 / len
            self.data *= invLen
        return self

    def dot( self, v ):
        '''Performs the dot product of this vector with the given vector.

        @param:     v       The vector to dot with this.
        @returns:   A scalar, the inner product of this with v.
        '''
        return np.dot( self.data, v.data )

    def copy( self ):
        '''Returns a unique copy of this vector.

        @returns:       A new Vector3 with the same, but independent values as this vector.
        '''
        return self.__class__( array = self.data )

    def minAxis( self ):
        """Returns the axis with the minimum value.

        If two dimensions contain an equally small value, the index will be the lower
        of the two.
        
        @returns:   The index of the dimension that contains the smallest
                    value (includes the full range of reals, positive and negative).
        """
        return self.data.argmin()

    def minAbsAxis( self ):
        """Returns the axis with the minimum absolute magnitude

        If two dimensions contain an equally small value, the index will be the lower
        of the two.
        
        @returns:   The index of the dimension with the smallest *magnitude*.
        """
        return np.abs( self.data ).argmin()

class Vector2( Vector ):
    '''A two-dimensional vector'''
    def __init__( self, x=0, y=0, array=None ):
        '''Constructor.

        The Vector can be initialized with either individual values or with the array keyword.
        If no arguments are provided, the zero vector is created.
        If the array argument is not None, then it is used to set the array data.
        Otherwise, the x, and y values can be explicitly passed.
        '''
        if ( array is not None ):
            assert( len( array ) == 2 )
            self.data = np.array( array, FLOAT )
        else:
            self.data = np.array( (x, y ), FLOAT )

    x = property( lambda self: self.data[0], lambda self, v: self.__setitem__( 0, v ) )
    y = property( lambda self: self.data[1], lambda self, v: self.__setitem__( 1, v ) )
    
    def __str__( self ):
        '''String representation of the Vector2.

        @returns:   A string representing this vector.
        '''
        return "Vector2<{0:.{2}f}, {1:.{2}f}>".format( self.data[0], self.data[1], PRINT_RESOLUTION )
        
class Vector3( Vector ):
    '''A three-dimensional vector.'''
    def __init__(self, x = 0, y = 0, z = 0, array = None ):
        '''Constructor.

        The Vector can be initialized with either individual values or with the array keyword.
        If no arguments are provided, the zero vector is created.
        If the array argument is not None, then it is used to set the array data.
        Otherwise, the x, y, and z values can be explicitly passed.
        '''
        if ( array is not None ):
            assert( len( array ) == 3 )
            self.data = np.array( array, FLOAT )
        else:
            self.data = np.array( (x, y, z ), FLOAT )
        
    def __repr__( self ):
        return "V3<{0:.{3}f}, {1:.{3}f}, {2:.{3}f}>".format( self.data[0], self.data[1], self.data[2], PRINT_RESOLUTION )

    def __str__( self ):
        return "Vector3<{0:.{3}f}, {1:.{3}f}, {2:.{3}f}>".format( self.data[0], self.data[1], self.data[2], PRINT_RESOLUTION )

    x = property( lambda self: self.data[0], lambda self, v: self.__setitem__( 0, v ) )
    y = property( lambda self: self.data[1], lambda self, v: self.__setitem__( 1, v ) )
    z = property( lambda self: self.data[2], lambda self, v: self.__setitem__( 2, v ) )

    def __mul__(self, s ):
        '''Multiplies this vector on the right by the given multiplicand.

        The multiplicand can be: a scalar, a vector of the same size, or a 3x3 matrix.

        @param:     m       The multiplicand.
        @returns:   A new vector instance.  If m is a scalar, then it contains the scaled values of
                    this vector.  If m is a vector of the same size, the new vector contains they
                    element-wise products of the two vectors.  If m is a matrix, it is a new Vector3.
        '''
        if ( isinstance( s, Matrix3x3 ) ):
            return Vector3( array = np.dot( self.data, s.data ) ) #np.dot automatically transposes this array to column
        elif ( isinstance( s, Matrix4x4 ) ):
               v4 = np.array( ( self.data[0], self.data[1], self.data[2], 1 ), dtype=FLOAT )
               return Vector3( array=np.dot( v4, s.data )[:3] )
        else:
            return Vector.__mul__( self, s )

    def cross( self, v ):
        '''Performs the cross product of this x v.

        @param:     v       The vector to cross with this one.  It must also be Vector3
        @returns:   A Vector3, the cross product.
        '''
        return self.__class__( array = np.cross( self.data[:], v.data[:] ) )

    def rotateVMatrix( self, angle ):
        '''Produces the matrix which will rotate around the given v the given amount.

        @param:     angle   The angle of rotation (in radians).
        @returns:   A new Matrix3x3 that when multiplied with a vector will rotate that
                    vector.
        '''
        try:
            assert( self.length() >= 1.0 - EPS and self.length() <= 1.0 + EPS )
        except AssertionError as e:
            len = self.length()
            print "Rotating around unnormalized vector: ", self, "with length %.6f" % len
            raise e
        c = np.cos(angle)
        s = np.sin(angle)
        omc = 1 - c
        x = self.x
        y = self.y
        z = self.z
        m = Matrix3x3( [[ x * x * omc + c, y * x * omc - z * s, z * x * omc + y * s ],
                     [ x * y * omc + z * s, y * y * omc + c, z * y * omc - x * s ],
                     [ x * z * omc - y * s, y * z * omc + x * s, z * z * omc + c ] ] )
        return m
    
    def rotateV( self, v, angle ):
        '''Rotate this vector around another Vector3 a given angle.

        @param:     v       The Vector3 around which this vector is to be rotated.
        @param:     angle   The angle of rotation (in radians).
        @returns:   A new Vector3 instance: the rotated version of this vector.
        '''
        #TODO: Replace this with quaternion rotation
        return self.rotateVMatrix() * self

    def rotateX( self, angle ):
        '''Rotates this vector around the x-axis by the given angle.

        @param:     angle       The amount of rotation (in radians) to apply.
        @returns:   A new Vector3; the rotated version of this matrix.
        '''
        newY, newZ = self.__rotatePair( angle, self.y, self.z )
        return Vector3( self.x, newY, newZ )

    def rotateY( self, angle ):
        '''Rotates this vector around the y-axis by the given angle.

        @param:     angle       The amount of rotation (in radians) to apply.
        @returns:   A new Vector3; the rotated version of this matrix.
        '''
        newZ, newX = self.__rotatePair( angle, self.z, self.x )
        return Vector3( newX, self.y, newZ )

    def rotateZ( self, angle ):
        '''Rotates this vector around the z-axis by the given angle.

        @param:     angle       The amount of rotation (in radians) to apply.
        @returns:   A new Vector3; the rotated version of this matrix.
        '''
        newX, newY = self.__rotatePair( angle, self.x, self.y )
        return Vector3( newX, newY, self.z )

    def __rotatePair( self, angle, a, b ):
        '''Performs a 2D rotation of the vector <a, b> around an axis orthogonal to the
        plane on which <a, b> lies.

        @param:     angle       The amount of rotation (in radians) to perform.
        @param:     a           The first element of the R2 vector.
        @param:     b           The second element of the R2 vector.
        @returns:   A 2-tuple containing the transformed a and b elements.
        '''
        c = np.cos( angle )
        s = np.sin( angle )
        newA = c * a - s * b
        newB = c * b + s * a
        return (newA, newB)
    

class Vector4( Vector ):
    '''A four-dimensional vector.  Interpreted as homogeneous 3D coordinates.'''        
    def __init__(self, x = 0, y = 0, z = 0, w = 1, array = None ):
        '''Constructor.

        The vector can be initialized with either individual values or with the array keyword.
        If no arguments are provided, the zero vector is created.
        If the array argument is not None, then it is used to set the array data.
        Otherwise, the x, y, z, and w values can be explicitly passed.
        '''
        if ( array is not None ):
            assert( len( array ) == 4 )
            self.data = np.array( array, FLOAT )
        else:
            self.data = np.array( (x, y, z, w ), FLOAT )

    def __repr__( self ):
        return "V4<{0:.{4}f}, {1:.{4}f}, {2:.{4}f}, {3:.{4}f}>".format( self.data[0], self.data[1], self.data[2], self.data[3], PRINT_RESOLUTION )

    def __str__( self ):
        return "Vector4<{0:.{4}f}, {1:.{4}f}, {2:.{4}f}, {3:.{4}f}>".format( self.data[0], self.data[1], self.data[2], self.data[3], PRINT_RESOLUTION )

    x = property( lambda self: self.data[0], lambda self, v: self.__setitem__( 0, v ) )
    y = property( lambda self: self.data[1], lambda self, v: self.__setitem__( 1, v ) )
    z = property( lambda self: self.data[2], lambda self, v: self.__setitem__( 2, v ) )
    w = property( lambda self: self.data[3], lambda self, v: self.__setitem__( 3, v ) )

    def __mul__(self, s ):
        '''Multiplies this vector on the right by the given multiplicand.

        The multiplicand can be: a scalar, a vector of the same size, or a 4x4 matrix.

        @param:     m       The multiplicand.
        @returns:   A new vector instance.  If m is a scalar, then it contains the scaled values of
                    this vector.  If m is a vector of the same size, the new vector contains they
                    element-wise products of the two vectors.  If m is a matrix, it is a new Vector3.
        '''
        if ( isinstance( s, Matrix4x4) ):
            return Vector4( array = np.dot( self.data, s.data ) ) #np.dot automatically transposes this array to column
        else:
            return Vector.__mul__( self, s )

    def getVector3( self ):
        """Returns a truncated Vector3 version of this vector.

        @returns:       A new Vector3 containing the x, y, and z elements of this vector.
        """
        return Vector3( self.x, self.y, self.z )

    def getHomoVector3( self ):
        """Returns a homogenized Vector3 version of this vector.

        The homogenzied coordinates are x, y, z are divided by w.

        @returns:       A new Vector3 containing the homogenized x, y, and z elements of this vector.
        """
        inv = 1.0 / self.w
        return Vector3( self.x * inv, self.y * inv, self.z * inv )

class Matrix3x3:
    '''A 3x3 matrix'''
    def __init__( self, data = None ):
        '''Constructor.

        Either constructs the default identity matrix or initializes the matrix to the provided
        data.

        @param:     data        Optional data to initialize the matrix.  If provided, it must be a 
                                3x3 numpy array of floats.
        '''
        if ( data is not None ):
            self.data = np.array( data )
            self.rows, self.cols = self.data.shape
            if ( self.rows != 3 or self.cols != 3 ):
                raise ValueError, "Matrix3x3 requires a 3 X 3 array to populate"
        else:
            self.data = np.eye( 3 )
            self.rows = 3
            self.cols = 3

    def __str__( self ):
        s = "Matrix3x3:\n"
        s += str( self.data )
        return s

    def __sub__( self, m ):
        '''Performs element-wise subtraction between this matrix and another.

        @param:     m       The matrix to subtract from this one.
        @returns:   A new Matrix3x3.
        '''
        if ( isinstance( m, Matrix3x3 ) ):
            return Matrix3x3( self.data - m.data )

    def __mul__( self, m ):
        '''Multiplies this matrix by a multiplicand on its right.

        The multiplicand can be a Vector3, another Matrix3x3 or a scalar.
            - if Vector3, the result is the Vector3 transformed by this matrix.
            - if Matrix3x3, the result is a new Matrix3x3 which is the product
            of this multiplied by m.
            - if scalar, the result is a new Matrix3x3 such that each element
            is multiplied by the scalar.

        @param:     m       The multiplicand.
        @returns:   A Vector3 if m is a Vector3, a Matrix3x3 if m is a scalar or
                    Matrix3x3.
        '''
        if ( isinstance(m, Vector3) ):
            return Vector3( array = np.dot( self.data, m.data ) )
        elif ( isinstance(m, Matrix3x3 ) ):
            return Matrix3x3( np.dot( self.data, m.data ) )
        elif( isinstance(m, int) or isinstance(m, float) or isinstance( m, np.integer ) or isinstance( m, np.floating ) ):
            return Matrix3x3( np.dot( self.data, m ) )
        else:
            raise ValueError, "Can't multiply object of type %s against a Matrix3x3" % (s.__class__.__name__)

    def __rmul__( self, m ):
        '''Multiplies this matrix by a *scalar* multiplicand on its left.

        This only works for scalars.

        @param:     m       The scalar multiplicand.
        @returns:   A new Matrix3x3 where each element is scaled by m.
        '''
        if( isinstance(m, int) or isinstance(m, float) or isinstance( m, np.integer ) or isinstance( m, np.floating ) ):
            return Matrix3x3( self.data * m )
        else:
            raise ValueError, "Can't multiply object of type %s against a Matrix3x3" % (s.__class__.__name__)

    def __getitem__( self, r, ):
        '''Retrieve the rth row of the matrix.

        @param:     r       The index of the desired row.
        @returns:   A numpy array of floats with shape (3,).  The rth row.
        @raises:    Index error if r is invalid.
        '''
        return self.data[r]

    def identity():
        """Returns an identity matrix.

        @returns:       A new Matrix3x3: the identiy matrix.
        """
        return Matrix3x3()

    def transpose( self ):
        '''Transposes the matrix.

        @returns:       A new Matrix3x3 where each elemetn (i,j) in the new matrix
                        comes from (j, i) in this matrix.
        '''
        return Matrix3x3( self.data.T )

    def getFlattened( self ):
        '''Returns a flattened version of the matrix.

        @returns:   A numpy array of floats with shape (1,9).  The elements are flattened in a row-major order.
        '''
        return self.data.flatten().tolist()

    def copy( self ):
        """Returns a copy of this matrix.

        @returns:       A new Matrix3x3 with the same numerical values as this matrix.
        """
        return self.__class__( data = self.data )
    
IDENTITY3x3 =    Matrix3x3()

class Matrix4x4:
    '''A 3x3 matrix'''
    def __init__( self, data = None ):
        '''Constructor.

        Either constructs the default identity matrix or initializes the matrix to the provided
        data.

        @param:     data        Optional data to initialize the matrix.  If provided, it must be a 
                                4x4 numpy array of floats.
        '''
        if ( data is not None ):
            self.data = np.array( data )
            self.rows, self.cols = self.data.shape
            if ( self.rows != 4 or self.cols != 4 ):
                raise ValueError, "Matrix4x4 requires a 4 X 4 array to populate"
        else:
            self.data = np.eye( 4 )
            self.rows = 4
            self.cols = 4

    def __str__( self ):
        s = "Matrix4x4:\n"
        s += str( self.data )
        return s

    def __sub__( self, m ):
        '''Performs element-wise subtraction between this matrix and another.

        @param:     m       The matrix to subtract from this one.
        @returns:   A new Matrix4x4.
        '''
        if ( isinstance( m, Matrix4x4 ) ):
            return Matrix4x4( self.data - m.data )
        
    def __mul__( self, m ):
        '''Multiplies this matrix by a multiplicand on its right.

        The multiplicand can be a Vector4, Vector3, another Matrix4x4 or a scalar.
            - if Vector4, the result is the new Vector4 transformed by this matrix.
            - if Vector3, the result is a Vector3.  It is the truncated, transformed Vector4
            created by promoting the V3 to V4 by providing a homogeneous value of 1.
            - if Matrix4x4, the result is a new Matrix4x4 which is the product
            of this multiplied by m.
            - if scalar, the result is a new Matrix4x4 such that each element
            is multiplied by the scalar.

        @param:     m       The multiplicand.
        @returns:   A Vector4 if m is a Vector4, Vector3 if m is a Vector3, a Matrix4x4 if m is a scalar or
                    Matrix4x4.
        '''
        if ( isinstance(m, Vector4 ) ):
            return Vector4( array = np.dot( self.data, m.data ) )
        elif ( isinstance(m, Vector3) ):
            # Project V3 into V4 by setting V4[3] = 1
            v = np.array( m.data.tolist() + [1] )
            return Vector3( array = np.dot( self.data, v )[:3] )
        elif ( isinstance(m, Matrix4x4 ) ):
            return Matrix4x4( np.dot( self.data, m.data ) )
        elif( isinstance(m, int) or isinstance(m, float) or isinstance( m, np.integer ) or isinstance( m, np.floating ) ):
            return Matrix4x4( self.data * m )
        else:
            raise ValueError, "Can't multiply object of type %s against a Matrix4x4" % (m.__class__.__name__)

    def __rmul__( self, m ):
        '''Multiplies this matrix by a *scalar* multiplicand on its left.

        This only works for scalars.

        @param:     m       The scalar multiplicand.
        @returns:   A new Matrix4x4 where each element is scaled by m.
        '''
        if( isinstance(m, int) or isinstance(m, float) or isinstance( m, np.integer ) or isinstance( m, np.floating ) ):
            return Matrix4x4( self.data * m )
        else:
            raise ValueError, "Can't multiply object of type %s against a Matrix4x4" % ( s.__class__.__name__ )

    def __getitem__( self, r ):
        '''Retrieve the rth row of the matrix.

        @param:     r       The index of the desired row.
        @returns:   A numpy array of floats with shape (3,).  The rth row.
        @raises:    Index error if r is invalid.
        '''
        return self.data[r]

    def identity( self ):
        """Returns an identity matrix.

        @returns:       A new Matrix4x4: the identiy matrix.
        """
        return Matrix4x4()

    def setIdentity( self ):
        """Returns an identity matrix.

        @returns:       A new Matrix4x4: the identiy matrix.
        """
        self.data[:,:] = np.eye( 4 )

    def transpose( self ):
        '''Transposes the matrix.

        @returns:       A new Matrix4x4 where each elemetn (i,j) in the new matrix
                        comes from (j, i) in this matrix.
        '''
        return Matrix4x4( self.data.T )

    def getFlattened( self ):
        '''Returns a flattened version of the matrix.

        @returns:   A numpy array of floats with shape (1,16).  The elements are flattened in a row-major order.
        '''
        return self.data.flatten().tolist()

    def setFromFlattened( self, data ):
        """Sets the matrix from a flattened array.

        @param:     data        A numpy array of floats with shape (1,16) or (16,) interpreted as row-major
                                values in the matrix.
        """
        data = np.array( data )
        if ( data.size != 16 ):
            raise ValueError, "Can't set Matrix4X4 with %d elements" % data.size
        else:
            self.data = data.copy()
            self.data.shape = (4, 4 )
            
    def copy( self ):
        """Returns a copy of this matrix.

        @returns:       A new Matrix4x4 with the same numerical values as this matrix.
        """
        return self.__class__( data = self.data )

    def set( self, mat ):
        '''Sets this matrix from the provided matrix.

        @param:     mat     A Matrix4x4.'''
        self.data[:, :] = mat.data[:,:]

    def setTranspose( self, mat ):
        '''Sets this matrix as the transpose of the provided matrix.

        @param:     mat     The matrix whose transpose will be set into this matrix.
        '''
        self.data[:, :] = mat.data.T[:, :]

    def setRow( self, row, x0, x1, x2, x3 ):
        '''Sets the row of the matrix.

        @param:     row     The row to target.
        @param:     x0      The value for the 0th element on the row.
        @param:     x1      The value for the 1st element on the row.
        @param:     x2      The value for the 2nd element on the row.
        @param:     x3      The value for the 3rd element on the row.
        '''
        self.data[ row, 0 ] = x0
        self.data[ row, 1 ] = x1
        self.data[ row, 2 ] = x2
        self.data[ row, 3 ] = x3

    def setDiagonal( self, x0, x1, x2, x3 ):
        '''Sets the digonal values (top-left to bottom-right).

        @param:     x0      The value for the (0,0) element.
        @param:     x1      The value for the (1,1) element.
        @param:     x2      The value for the (2,2) element.
        @param:     x3      The value for the (3,3) element.
        '''
        self.data[0, 0] = x0
        self.data[1, 1] = x1
        self.data[2, 2] = x2
        self.data[3, 3] = x3
               
            
def homogenize3x3( m ):
    """Converts a 3x3 matrix to 4x4 by adding 0's and a single 1.

    param:      m       A Matrix3x3 to use as the basis for this matrix.
    """
    return Matrix4x4( [ m.data[0].tolist() + [0],
                        m.data[1].tolist() + [0],
                        m.data[2].tolist() + [0],
                        [ 0, 0, 0, 1] ] )

IDENTITY4x4 = Matrix4x4()

def createXRotateMatrix4( angle ):
    '''Creates a matrix to rotate around the x-axis.

    @param:     angle       The angle of rotation (in radians).
    @returns:   A new Matrix4x4.
    '''
    cx = np.cos( angle )
    sx = np.sin( angle )
    return Matrix4x4( [[1, 0,   0,  0],
                       [0, cx,  -sx, 0],
                       [0, sx, cx, 0],
                       [0, 0,   0,  1] ] )

def createYRotateMatrix4( angle ):
    '''Creates a matrix to rotate around the y-axis.

    @param:     angle       The angle of rotation (in radians).
    @returns:   A new Matrix4x4.
    '''
    # see createYRotateMatrix3 for the explanation of why the sine terms are transposed
    cx = np.cos( angle )
    sx = np.sin( angle )
    return Matrix4x4( [[cx,  0,  sx, 0],
                       [0,   1,  0,  0],
                       [-sx, 0,  cx, 0],
                       [0,   0,  0,  1] ] )

def createZRotateMatrix4( angle ):
    '''Creates a matrix to rotate around the z-axis.

    @param:     angle       The angle of rotation (in radians).
    @returns:   A new Matrix4x4.
    '''
    cx = np.cos( angle )
    sx = np.sin( angle )
    return Matrix4x4( [[cx,  -sx, 0, 0],
                       [sx, cx, 0, 0],
                       [0,   0,  1, 0],
                       [0,   0,  0, 1] ] )

def createXRotateMatrix3( angle ):
    '''Creates a matrix to rotate around the x-axis.

    @param:     angle       The angle of rotation (in radians).
    @returns:   A new Matrix3x3.
    '''
    cx = np.cos( angle )
    sx = np.sin( angle )
    return Matrix3x3( [[1, 0,   0],
                       [0, cx, -sx],
                       [0, sx, cx] ] )

def createYRotateMatrix3( angle ):
    '''Creates a matrix to rotate around the y-axis.

    @param:     angle       The angle of rotation (in radians).
    @returns:   A new Matrix3x3.
    '''
    # NOTE - note that the position of sx and -sx are transposed from the other matrices
    #   This is because looking down the Z.cross( X ) = Y
    #   That implies that the 90-degree range between Z and X STARTS at Z and sweeps
    #   counter-clockwise to X.  In other words, Z is the horizontal and X is the vertical axis.
    #   So, transposing this matrix will implicitly perform this switch.
    cx = np.cos( angle )
    sx = np.sin( angle )
    return Matrix3x3( [[cx,  0,  sx],
                       [0,   1,  0],
                       [-sx,  0,  cx] ] )

def createZRotateMatrix3( angle ):
    '''Creates a matrix to rotate around the z-axis.

    @param:     angle       The angle of rotation (in radians).
    @returns:   A new Matrix3x3.
    '''
    cx = np.cos( angle )
    sx = np.sin( angle )
    return Matrix3x3( [[cx, -sx, 0],
                       [sx,  cx, 0],
                       [0,    0,  1] ] )

if __name__ == "__main__":
    def testR3V():
        testVec( Vector3, "Testing R3 Vector" )

    def testR4V():
        testVec( Vector4, "Testing R4 Vector" )
        
    def testVec( V, msg ):
        ANGLE = 30
        print msg
        v1 = V(1, 2, 3)
        print "\tAccess"
        print "\tv1:", v1
        print "\tv1.x =", v1.x
        print "\tv1.y =", v1.y
        print "\tv1.z =", v1.z
        print "\tv1.[0] =", v1[0]
        print "\tv1.[1] =", v1[1]
        print "\tv1.[2] =", v1[2]
        print "\tv1.getTuple() =", v1.getTuple()
        print "\tv1.getList() =", v1.getList()
        v1.x = 10
        print "\tv1.x = 10", v1
        v1.y = 20
        print "\tv1.y = 20", v1
        v1.z = 30
        print "\tv1.z = 30", v1

        print "\n\tMath"
        print "\tscalar"
        try:
            res = v1 + 3
            print "ERROR! Allowed vector plus scalar"
        except AttributeError:
            print "\t\tv1 + scalar is not allowed!"
        try:
            v1 += 3
            print "ERROR! Allowed vector in-place plus scalar"
        except AttributeError:
            print "\t\tv1 += scalar is not allowed!"
        print "\t\tv1 * 3 =", ( v1 * 3 )
        print "\t\t3 * v1 =", ( 3 * v1 )
        print "\tvector"
        v2 = V(4, 5, 6 )
        print "\t\tv2 =", v2
        print "\t\tv1 + v2 =", (v1 + v2 )
        print "\t\tv2 + v1 =", (v2 + v1 )
        print "\t\tv1 - v2 =", (v1 - v2 )
        print "\t\tv2 - v1 =", (v2 - v1 )
        v1 += v2
        print "\t\tv1 += v2 -->", v1
        print "\t\tv1 =", v1, ", ||v1|| =", v1.length()
        print "\t\tv2 =", v2, ", ||v2|| =", v2.length()
        print "\t\tv1/||v1|| =", v1.normalize()
        print "\t\tv2/||v2|| =", v2.normalize()
        print "\t\tv1 . v2 =", v1.dot( v2 )
        try:
            x = v1.cross( v2 )
            print "\t\tv1 x v2 =", x
            print "\t\tv2 x v1 =", v2.cross( v1 )
        except AttributeError:
            print '\t\t%s has no cross function' % V.__name__
        v1.normalize_ip()
        v2.normalize_ip()
        print "\t\tv1/||v1|| =", v1.normalize()
        print "\t\tv2/||v2|| =", v2.normalize()
        print "\t\tv1 . v2 =", v1.dot( v2 )
        try:
            x = v1.cross( v2 )
            print "\t\tv1 x v2 =", x
            print "\t\tv2 x v1 =", v2.cross( v1 )
            v1.x = v1.z = 0
            v1.y = 1
            print "\t\tv1:", v1
            v = v1.rotateV( V( 1, 1, 1), ANGLE * ANGTORAD )
            print "\t\tRotated %d degrees around (1, 1, 1)" % (ANGLE), v
            v = v1.rotateV( V( 1, 0, ), ANGLE * ANGTORAD )
            print "\t\tRotated %d degrees around (1, 0, 0)" % (ANGLE), v
            v = v1.rotateX( ANGLE * ANGTORAD )
            print "\t\tRotate %d degrees around x         " % (ANGLE), v
            v1.x = 1
            v1.y = 0
            print "\t\tv1:", v1
            v = v1.rotateV( V( 0, 1, 0), ANGLE * ANGTORAD )
            print "\t\tRotated %d degrees around (0, 1, 0)" % (ANGLE), v
            v = v1.rotateY( ANGLE * ANGTORAD )
            print "\t\tRotate %d degrees around y         " % (ANGLE), v
            v = v1.rotateV( V( 0, 0, 1), ANGLE * ANGTORAD )
            print "\t\tRotated %d degrees around (0, 0, 1)" % (ANGLE), v
            v = v1.rotateZ( ANGLE * ANGTORAD )
            print "\t\tRotate %d degrees around z         " % (ANGLE), v
        except:
            pass
        
        v1 = V( 2, 3, 4 )
        v = v1 * v1
        print "\t\tv1 .* v1", v
        v2 = v1.copy()
        v2.y = 32
        print "\t\t%s != %s" % ( v1, v2 )
        

    def testR3M():
        testMatrix( Matrix3x3, Vector3, "Testing R3 Matrix" )

    def testR4M():
        testMatrix( Matrix4x4, Vector4, "Testing R4 Matrix" )

    def testMatrix( M, V, msg ):
        print msg
        m = M()
        print "\tm\n", m
        ANGLE = 30
        xRot = createXRotateMatrix3( ANGLE * ANGTORAD )
        print "\t%d-degree x-rotation\n" % ( ANGLE ), xRot
        yRot = createYRotateMatrix3( ANGLE * ANGTORAD )
        print "\t%d-degree y-rotation\n" % (ANGLE), yRot
        zRot = createZRotateMatrix3( ANGLE * ANGTORAD )
        print "\t%d-degree z-rotation\n" % (ANGLE), zRot
        v = V( 0, 1, 0 )
        print "\tv", v
        print "\tX * v", xRot * v
        v = V( 1, 0, 0 )
        print "\tv", v
        print "\tY * v", yRot * v
        print "\tZ * v", zRot * v
        m[0][0] = 0
        m[0][1] = 1
        m[1][0] = 1
        m[1][1] = 0
        v = V( 1, 2, 3 )
        print "\tv", v
        print "\tm\n", m
        print "\tM * v", m * v
        print "\tM - I\n", m - M()
        print "\tM * 2\n", m * 2
        print "\tM * X\n", m * xRot
        print "\tX.transpose()\n", xRot.transpose()
        print "\tX.flat", xRot.getFlattened()

    def glTest():
        M = Matrix4x4
        m = M()
        print "\nIdentity\n", m
        ANGLE = 30
        xRot = createXRotateMatrix4( ANGLE * ANGTORAD )
        print "\nRotate X - %d degrees\n" % ( ANGLE ), xRot
        yRot = createYRotateMatrix4( ANGLE * ANGTORAD )
        print "\nRotate Y - %d degrees\n" % ( ANGLE ), yRot
        zRot = createZRotateMatrix4( ANGLE * ANGTORAD )
        print "\nRotate Z - %d degrees\n" % ( ANGLE ), zRot
        rot = yRot * xRot
        print "\nRotate X(%d), then Y(%d)\n" % ( ANGLE, ANGLE), rot
##    glTest()
    testR3V()
##    testR4V()
##    testR3M()
##    
##    v1 = Vector3(0, 1, 0)
##    print "2 * v1", (2 * v1)
##    print "v1 * 3", (v1 * 3)
##    try:
##        print "v1 * v1", (v1 * v1)
##    except ValueError, inst:
##        print inst.__class__.__name__, inst.args
##
##    m1 = Matrix3x3([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
##    m2 = Matrix3x3([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
##    print "m1 * m2", (m1 * m2)
##    print "m1 * v1", (m1 * v1)
##    print "v1 * m1", (v1 * m1)
##    print "m1 * 3", (m1 * 3)
##    print "3 * m1", (3 * m1)
##
    