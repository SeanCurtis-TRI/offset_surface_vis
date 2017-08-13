# implementation of quaternions.
import numpy as np
from matrix import Vector3 as V3
from matrix import Matrix3x3 as M3
from matrix import PRINT_RESOLUTION

# TODO:
#   maybe it would be better to define the Quaternion as scalar, vector since many of the operations are expressed as such.
#   I'll use a numpy array to do this (then I get some operations for free.

# Quaternion operations
def _realProduct( p, q ):
    '''Computes the real portion of the quaternion multiplication pq.

    @param:     p       The first quaternion.
    @param:     q       The second quaternion.
    @returns:   A scalar representing the real portion of the product.
    '''
    return p.t * q.t - p.v.dot( q.v )

def _vecProduct( p, q ):
    '''Computes the vector portion of the quaternion multiplication pq.

    @param:     p       The first quaternion.
    @param:     q       The second quatenrion.
    @returns:   The vector portion (instance of V3) of the multiplication.
    '''
    return p.t * q.v + p.v * q.t + p.v.cross( q.v )

class Quaternion:
    '''A quaternion class for representing orientation and rotations'''
    # the minimum L-infinity error threshold between two quaternions to determine equivalency
    SAME_THRESHOLD = 1e-5
    
    def __init__( self, t=1.0, u=0.0, v=0.0, w=0.0 ):
        self.t = t                          # the real portion
        self.v = V3( array=(u, v, w ) )      # The imaginary portion of the quaternion

    def __str__( self ):
        '''String representation of the quaternion'''
        return 'Q: {0:.{4}f} <{1:.{4}f}, {2:.{4}f}, {3:.{4}f}>'.format( self.t, self.v[0], self.v[1], self.v[2], PRINT_RESOLUTION )
    
    # Mathematical operators
    def __add__( self, q ):
        '''Adds this quaternion to the given quaternion and returns the result.

        @param:     q       The quaternion to add.
        @returns:   A new Quaternion containing the addition (an element-wise addition).
        '''
        assert( isinstance( q, Quaternion ) )
        v = self.v + q.v
        return Quaternion( self.t + q.t, v[0], v[1], v[2] )
    
    def __sub__( self, q ):
        '''Subtracts the given quaternion from this quaternion and returns the result.

        @param:     q       The quaternion to subtract.
        @returns:   A new Quaternion containing the addition (an element-wise addition).
        '''
        assert( isinstance( q, Quaternion ) )
        v = self.v - q.v
        return Quaternion( self.t - q.t, v[0], v[1], v[2] )
    
    def __div__( self, scalar ):
        '''Division by a scalar.

        @param:     scalar      A float (or int) scalar.
        @returns:   A new quaternion scaled by the inverse of the scalar value.
        '''
        assert( isinstance( scalar, float ) or isinstance( scalar, int ) or
                isinstance( scalar, np.floating ) or isinstance( scalar, np.integer ) )
        invS = 1.0 / scalar
        return Quaternion( self.t * invS, self.v[0] * invS, self.v[1] * invS, self.v[2] * invS )
    
    def __mul__( self, m ):
        '''Multiplication by a scalar or quaternion.

        @param:     m       The multiplicand.  A float (or int) scalar.
        @returns:   A new quaternion.  The scaled quaternion if m is a scalar, or the hamiltonian
                    product if m is a quaternion.
        '''
        if( isinstance( m, float ) or isinstance( m, int ) or
            isinstance( m, np.floating ) or isinstance( m, np.integer ) ):
            return Quaternion( self.t * m, self.v[0] * m, self.v[1] * m, self.v[2] * m )
        elif ( isinstance( m, Quaternion ) ):
            t = _realProduct( self, m )
            v = _vecProduct( self, m )
            return Quaternion( t, v[0], v[1], v[2] )

    def __eq__( self, q ):
        '''Reports if the two quaternions are the same.  Same is that the L-infinity norm of the
        difference between the two quaternions is below a global threshold.

        @param:     q       The quaternion to compare.
        @returns:   True if they are the "same", False otherwise.
        '''
        p = self - q
        err = max( abs( p.t ), abs( p.v[0] ), abs( p.v[1] ), abs( p.v[2] ) )
        return err <= self.SAME_THRESHOLD
    
    def magnitude( self ):
        '''Compute the magnitude of the quaternion.

        @returns:   A single scalar float representing the magnitude of the Quaternion.
        '''
        return np.sqrt( self.magnitudeSq() )

    def magnitudeSq( self ):
        '''Compute the squared magnitude of the quaternion.

        @returns:  A single scalar float representing the squared magnitude of the Quaternion.
        '''
        return self.t * self.t + self.v.dot( self.v )

    def inverse( self ):
        '''Returns the multiplicative inverse of this quaternion.

        @returns:   A quaternion which, when multiplied to this quaternion, produces the result <1, 0, 0, 0>
        '''
        return self.conjugate() / self.magnitudeSq()

    def conjugate( self ):
        '''Returns the conjugate of this quaternion.
        If this quaternion is < t, u, v, w >, its conjugate is < t, -u, -v, -w >.

        @returns:   A new quaternion, the conjugate of this one.
        '''
        return Quaternion( self.t, -self.v[0], -self.v[1], -self.v[2] )

    def normalize( self ):
        '''Returns a normalized version of this quaternion.

        @returns:       A new quaternion whose magnitude is one.
        '''
        d = 1.0 / self.magnitude()
        v = self.v * d
        return Quaternion( self.t * d, v[0], v[1], v[2] )

    def rotate( self, v ):
        '''Rotates the given vector by this quaternion.
        If this quaternion is not a proper versor, then the result is not predictable.

        @param:     v       An instance of Vector3.  The value in R3 to rotate.
        @returns:   A new instance of Vector3 - the rotated value.
        '''
        p = Quaternion( 0.0, v[0], v[1], v[2] )
        # TECHNICALLY, this should be self.inverse() instead of self.conjugate()
        #   however, we're stipulating that this quaternion already has normal length, so
        #   the inverse IS the conjugate.
        return ( self * p * self.conjugate() ).v

    def rotMatrix( self ):
        '''Interprets this quaternion as a rotation quaternion and returns the corresponding
        3x3 rotation matrix.  If this quaternion is not unit-length, the resultant matrix will
        have a scaling factor as well.

        @returns:       A Matrix3x3.  The equivalent rotation matrix.
        '''
        v, a = self.axisAngle()
        c = np.cos( a )
        s = np.sin( a )
        omc = 1 - c
        r0 = ( c + v.x * v.x * omc, v.x * v.y * omc - v.z * s, v.x * v.z * omc + v.y * s )
        r1 = ( v.y * v.z * omc + v.z * s, c + v.y * v.y * omc, v.y * v.z * omc - v.x * s )
        r2 = ( v.z * v.x * omc - v.y * s, v.z * v.y * omc + v.x * s, c + v.z * v.z * omc )
        return M3( data=( r0, r1, r2 ) )

    def axisAngle( self ):
        '''Computes the axis-angle representation of this quaternion.
        If this quaternion is not unit-length, the results will be incorrect.  It is the
        caller's responsibility to guarantee that it is unit-length.

        @param:     A 2-tuple, (axis, angle).  Where axis is an instance of Vector3 (the axis
                    around which the rotation occurs) and angle is the rotation amount in radians.
        '''
        # extract the angle
        #   do it in a numerically stable manner
        #   angle = 2 arccos( self.t ) = 2 arcsin( self.v.length() )
        #   I'd rather do the arccos, but I'll get bad numbers when |self.t| is "close" to one.
        #       a small perturbation in self.t can lead to a large change in angle.
        #   So, i'll use the sine if |self.t| is > some magical limit
        if ( abs( self.t ) <= 0.8 ):
            # cosine stable
            hAngle = np.arccos( self.t )
        else:
            # cosine UNstable
            hAngle = np.arcsin( self.v.length() )
        angle = 2.0 * hAngle
        axis = self.v * ( 1.0 / np.sin( hAngle ) )
        
        return axis, angle

# utiliies for generating quaternions
def axisAngleQuat( axis, angle ):
    '''Creates a quaternion based on an axis-angle representation.

    @param:     axis        A unit vector around which the rotation is performed.
    @param:     angle       The amount of rotation (in radians).
    '''
    assert( axis.lengthSq() == 1.0 )
    hA = angle * 0.5
    c = np.cos( hA )
    s = np.sin( hA )
    v = s * axis
    return Quaternion( c, v[0], v[1], v[2] )

if __name__ == '__main__':
    print "Testing quaternions"
    Q = Quaternion
    one = Q( 1.0, 0.0, 0.0, 0.0 )
    neg1 = Q( -1.0, 0.0, 0.0, 0.0 )
    i = Q( 0.0, 1.0, 0.0, 0.0 )
    j = Q( 0.0, 0.0, 1.0, 0.0 )
    k = Q( 0.0, 0.0, 0.0, 1.0 )
    print '\t1:', one
    print '\t-1:', neg1
    print '\ti:', i
    print '\tj:', j
    print '\tk:', k
    print "\nTesting i^2 = j^2 = k^2 = ijk = -1"
    i2 = i * i
    print '\ti^2:', i2, i2 == neg1
    j2 = j * j
    print '\tj^2:', j2, j2 == neg1
    k2 = k * k
    print '\tk^2:', k2, k2 == neg1
    ijk = i * j * k
    print '\tijk:', ijk, ijk == neg1

    print '\nInverse (and, by implication, conjugate)'
    print '\tii^-1', i * i.inverse() == one
    print '\tjj^-1', j * j.inverse() == one
    print '\tkk^-1', k * k.inverse() == one
    print '\t11^-1', one * one.inverse() == one 
    print '\t-1-1^-1', neg1* neg1.inverse() == one 

    print '\nScaling'
    print '\ti * 3:', ( i * 3 ) == Q( 0.0, 3.0, 0.0, 0.0 )
    print '\ti / 3:', ( i / 3 ) == Q( 0.0, 1.0/3.0, 0.0, 0.0 )
    print '\tj * 4:', ( j * 4 ) == Q( 0.0, 0.0, 4.0, 0.0 )
    print '\tj / 4:', ( j / 4 ) == Q( 0.0, 0.0, 1.0/4.0, 0.0 )
    print '\tk * 5:', ( k * 5 ) == Q( 0.0, 0.0, 0.0, 5.0 )
    print '\tk / 5:', ( k / 5 ) == Q( 0.0, 0.0, 0.0, 1.0/5.0 )
    print '\t-1 * 6:', ( neg1 * 6 ) == Q ( -6.0, 0.0, 0.0, 0.0 )
    print '\t-1 / 6:', ( neg1 / 6 ) == Q( -1.0/6.0, 0.0, 0.0, 0.0 )

    print '\nRotation'
    angle = 45.0 / 180.0 * np.pi
    v = V3( 1.0, 0.0, 0.0 )
    X = V3( 1.0, 0.0, 0.0 )
    xQ = axisAngleQuat( X, angle )
    vR = xQ.rotate( v )
    print '\tRotate {0} {1} degrees around {2}'.format( v, angle * 180.0 / np.pi, X ), (v - vR).length() < 1e-5
    v = V3( 1.0, 1.0, 0.0 )
    vR = xQ.rotate( v )
    vTgt = V3( v[0], np.cos( angle ), np.cos( angle ) ) # this is not GENERALLY true
    print '\tRotate {0} {1} degrees around {2}'.format( v, angle * 180.0 / np.pi, X ), ( vTgt - vR).length() < 1e-5
    ax, ang = xQ.axisAngle()
    print '\tRestored angle:', abs( ang - angle ) < 1e-5
    print '\tRestored axis:', ( ax - X ).length() < 1e-5
    m = xQ.rotMatrix()
    vRM = m * v
    print '\tRotate {0} {1} degrees around {2} (matrix)'.format( v, angle * 180.0 / np.pi, X ), ( vTgt - vRM).length() < 1e-5