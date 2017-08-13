# The definition of a viewport camera

from matrix import *
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective, gluPickMatrix
import numpy as np
from copy import deepcopy

Y_UP = True
X = Vector3( 1.0, 0.0, 0.0 )
Y = Vector3( 0.0, 1.0, 0.0 )
Z = Vector3( 0.0, 0.0, 1.0 )
ZERO3 = Vector3( 0.0, 0.0, 0.0 )

if ( Y_UP ):
    WORLD_UP = Vector3( 0.0, 1.0, 0.0 )
    DEF_TARGET = Vector3( 0.0, 0.0, 1.0 )
    DEF_FACING = Vector3( 0.0, 0.0, 1.0 )
else:
    # Z-up
    WORLD_UP = Vector3( 0.0, 0.0, 1.0 )
    DEF_TARGET = Vector3( 0.0, 1.0, 0.0 )
    DEF_FACING = Vector3( 0.0, 1.0, 0.0 )

class CameraException( Exception ):
    pass

class CameraMatrix:
    '''A 4x4 matrix with particular semantics for camera transformations.

    It is provided as a convenience for camera controllers so that if there is extra
    data that needs to be updated with the camera transformation they can easily be
    performed.'''
    
    #   Only provides facilities for RIGID transformations (i.e. no skew or scale)
    #   Able to multiply Vector3 (by implicitly assigning them a homogenous coordinate
    #   Structure of xform matrix is:
    #       [ Ux Vx Wx tx ]
    #       [ Uy Vy Wy ty ]
    #       [ Uz Vz Wz tz ]
    #       [ 0  0  0  1  ]
    #   It is assumed that the vectors U, V, W are all orthonomal.
    #   Transforming points is achieved by right multiplying the column vector.

    def __init__( self, U=X, V=Y, W=Z, t=ZERO3, mat=None ):
        '''Constructor.

        To save on time, the matrix does NOT copy the input vectors.  The caller is responsible for
        providing parameters that will not be mutated outside the lifespan of this matrix.

        @param:     U       The direction of the new x-axis.
        @param:     V       The direction of the new y-axis.
        @param:     W       The direction of the new z-axis.
        @param:     t       The translation vector.
        @param:     mat     Optional initialization with a 3x3 rotation matrix.
        '''
        if ( mat ):
            self.U = Vector3( array=mat[ 0 ] )
            self.V = Vector3( array=mat[ 1 ] )
            self.W = Vector3( array=mat[ 2 ] )
        else:
            assert( U.dot( W ) < EPS )
            assert( U.dot( V ) < EPS )
            assert( V.dot( W ) < EPS )
            self.U = U
            self.V = V
            self.W = W
        self.t = t
                  
    def transform( self, v ):
        '''If this matrix is M, performs the calculation: Mv.

        @param:     v       The vector to transform.
        @retruns:   A new Vector3, transformed by this camera matrix.
        '''
        x = self.U.dot( v ) + self.t.x
        y = self.V.dot( v ) + self.t.y
        z = self.W.dot( v ) + self.t.z
        return Vector3( x, y, z )
    
class Camera:
    '''The basic, conceptual camera.  Responsible for understanding orientation and transformation of the camera.

    This is an "initial-state" camera.  I.e. to perform camera manipulation, camera "start" is called.  This caches
    the camera state and transformations are always done relative to the initial start state.  Likewise, the work
    can be canceled and restored to the initial state.  
    '''

    def __init__( self, pos=Vector3(0.0,0.0,0.0), facing=DEF_FACING, up=WORLD_UP, fov=45.0 ):
        '''Constructor.

        NOTE: The constructor copies the input vectors such that it has its own unique copy.  The camera's
        final up vector may not be the same as the input vector if the facing direction is not perpendicular
        to the given up direction

        @param:     pos         The position of the camera.
        @param:     facing      The direction in which the camera is looking.
        @param:     up          The up direction of the camera.
        @param:     fov         The horizontal field of view of the camera (in degrees).
        '''
        self.pos = pos
        
        self.facing = facing
        if ( self.facing.lengthSq() != 1.0 ):
            self.facing.normalize_ip()
            
        self.up = up
        if ( self.up.lengthSq() != 1.0 ):
            self.up.normalize_ip()

        assert( self.up.dot( self.facing ) < ( 1 - EPS ) )
        
        self.fov = fov
    
        self.right = self.facing.cross( self.up )
        self.up = self.right.cross( self.facing )

    def __str__( self ):
        return 'Camera @ {0}\n\tfacing: {1}\n\tup: {2}\n\tright: {3}'.format( self.pos, self.facing, self.up, self.right )

    def setFrom( self, camera ):
        '''Sets this camera's attributes from the given camera.

        @param:     camera      An instance of a Camera.
        '''
        self.pos.set( camera.pos )
        self.facing.set( camera.facing )
        self.up.set( camera.up )
        self.right.set( camera.right )
        self.fov = camera.fov

    # camera operations - moving, rotating, zooming, etc.

    def lookAt( self, target, up=WORLD_UP ):
        '''Aims the camera at the given target point, while trying to keep the top of the camera
        in the up direction.

        If the direction from camera position to target is parallel with the up direction, OR
        if the target and camera position are the same (within a threshold) a
        camera exception is raised. 

        @param:     target      A Vector3 indicating the point at which the camera should aim.
        @param;     up          A Vector3 indicating which direction is up for the camera.
        '''
        assert( up.lengthSq() == 1 )
        facing = target - self.pos
        distSq = facing.lengthSq()
        if ( distSq < EPS ):
            raise CameraException( "Target position same as camera position" )
        if ( distSq != 1.0 ):
            facing.normalize_ip()
        if ( abs( 1.0 - abs( facing.dot( up ) ) ) < EPS ):
            raise CameraException( "Facing direction is parallel with the up direction" )
        
        self.facing.set( facing )
        self.right.set( self.facing.cross( up ) )
        self.right.normalize_ip()
        self.up.set( self.right.cross( self.facing ) )

    def orbit( self, v, h, origin ):
        '''Causes the camera to rotate around a line passing through the given origin.

        @param:     v       The amount of rotation around the world's up axis.
        @param:     h       The amount of rotation around the the camera's right axis.
        @param:     origin  The point around which the camera orbits.
        @returns:   A matrix representing the full transformation of the camera.
        '''
        tilt = self.right.rotateVMatrix( h )
        pan = WORLD_UP.rotateVMatrix( v )
        m = pan * tilt
        self.facing.set( ( m * self.facing ).normalize() )
        self.up.set( ( m * self.up ).normalize() )
        self.right.set( ( m * self.right ).normalize() )
        mat = CameraMatrix( mat=m )  
        if ( origin is not None ):
            X = self.pos - origin
            XNew = m * X
            t = XNew - X
            mat.t = t
            self.pos.set( XNew + origin )
            
        return  mat
    
    def tilt( self, amount, origin=None ):
        '''Causes the camera to rotate around a line passing through the given origin, parallel with the camera's "right" axis.

        Positive values cause the camera to tilt upward, negative tilt downwards.
        With no origin defined, this is the traditional camera tilt.
        With an origin defined, there can be two effects:
            If the origin is in the facing direction, the camera performs a horizontal
            orbit around the origin.
            If the origin is NOT in the facing direction, an awkward rotation is performed.

        @param:     amount      The tilt amount (in radians).
        @param:     origin      The origin of rotation.  If none is specified, the camera's position is used.
        '''
        # compute rotation matrix
        tilt = self.right.rotateVMatrix( amount )
        self.right.set( ( tilt * self.right ).normalize() )
        self.facing.set( ( tilt * self.facing ).normalize() )
        self.up.set( ( tilt * self.up ).normalize() )
        mat = CameraMatrix( mat=tilt )            
        if ( origin is not None ):
            X = self.pos - origin
            XNew = tilt * X
            t = XNew - X
            mat.t = t
            self.pos.set( XNew + origin )
        return mat

    # pitch and tilt are exactly the same
    pitch = tilt

    def pan( self, amount, origin=None ):
        '''Causes the camera to rotate around an axis parallel with the world's up direction through the given origin.

        Positive values cause the camera to turn to the left, negative to the right.

        @param:     amount      The pan amount (in radians).
        @param:     origin      The origin of rotation.  If none is specified, the camera's position is used.
        @returns:   A matrix representing the camera's transformation.
        '''
        panM = createYRotateMatrix3( amount )
        self.right.set( ( panM * self.right ).normalize() )
        self.facing.set( ( panM * self.facing ).normalize() )
        self.up.set( ( panM * self.up ).normalize() )
        mat = CameraMatrix( mat=panM )            
        if ( origin is not None ):
            X = self.pos - origin
            XNew = panM * X
            t = XNew - X
            mat.t = t
            self.pos.set( XNew + origin )
        return mat
    
    def yaw( self, amount, origin=None ):
        '''Causes the camera to rotate around an axis parallel with its own up direction through the given origin.

        This is the same as pan, if the camera's up axis is parallel with the world up.
        Positive value causes the camera to turn to the left, negative to the right.

        @param:     amount      The yaw amount (in radians).
        @param:     origin      The origin of rotation.  If none is specified, the camera's position is used.
        @returns:   A matrix representing the camera's transformation.
        '''
        pass

    def roll( self, amount, origin=None ):
        '''Causes the camera to rotate around an axis parallel with its own facing direction, through the given origin.

        Positive values cause the camera to rotate clockwise, negative counter-clockwise.
        (NOTE: if the camera rotates clockwise, the viewed world will appear to rotate in a counter-clockwise fashion.)

        @param:     amount      The roll amount (in radians).
        @param:     origin      The origin of rotation.  If none is specified, the camera's position is used.
        @returns:   A matrix representing the camera's transformation.
        '''
        pass
    
    def zoom( self, amount ):
        '''Change the field of view (and implicitly the focal length) of the camera.

        Wider field of views approximate a shorter focal length and lead to a fish-eye lens quality.
        Narrow field of views approximate a longer focal length and lead to telephoto lens characteristics.

        The field of view is clamped to the range [EPS, 180]

        @param:     amount      The amount (in degrees) of the change to the field of view.
        @returns:   A boolean reporting if the field of view changed.
        '''
        newFOV = self.fov + amount
        if ( newFOV < EPS ):
            if ( self.fov == self.EPS ):
                # only reason I won't change is because I'm saturating at min field of view and am already there.
                return False
            # saturate to min focal length
            newFOV = EPS
        self.fov = newFOV
        return True
    
    def pedestalWorld( self, amount ):
        '''Change the camera position along the world's vertical axis without changing camera orientation.
        
        Positive values move up, negative move down.

        @param:     amount      The distance (in meters) to move the camera.
        @returns:   A matrix representing the camera's transformation.
        '''
        displace = WORLD_UP * amount
        self.pos += displace
        return CameraMatrix( t=displace )

    def pedestal( self, amount ):
        '''Change the camera position along the camera's vertical axis without changing camera orientation.
        
        Positive values move up, negative move down.

        @param:     amount      The distance (in meters) to move the camera.
        @returns:   A matrix representing the camera's transformation.
        '''
        displace = self.up * amount
        self.pos += displace
        return CameraMatrix( t=displace )

    def dollyWorld( self, amount ):
        '''Causes the camera to change position by moving the camera in the direction of the camera's
        facing direction projected on the ground.  The camera will maintain elevation and move parallel with the ground.

        Positive values cause the camera to move forward, negative backward.

        @param:     amount      The amount to move the camera (in meters).
        @returns:   A matrix representing the camera's transformation.
        '''
        dir = ( self.facing - ( self.facing.dot( WORLD_UP ) * WORLD_UP ) ).normalize()
        displace = dir * amount
        self.pos += displace
        return CameraMatrix( t=displace )

    def dolly( self, amount ):
        '''Causes the camera to change position by moving the camera in its facing direction.
        If the facing direction is not perpendicular with the world's up, the camera WILL change elevation.

        Positive values cause the camera to move forward, negative backward.

        @param:     amount      The amount to move the camera (in meters).
        @returns:   A matrix representing the camera's transformation.
        '''
        displace = self.facing * amount
        self.pos += displace
        return CameraMatrix( t=displace )

    def truckWorld( self, amount ):
        '''Causes the camera to change position by moving the camera in the direction of the camera's
        right direction projected on the ground.  The camera will maintain elevation and move parallel with the ground.

        Positive values cause the camera to move right, negative left.

        @param:     amount      The amount to move the camera (in meters).
        @returns:   A matrix representing the camera's transformation.
        '''
        dir = ( self.right - ( self.right.dot( WORLD_UP ) * WORLD_UP ) ).normalize()
        displace = dir * amount
        self.pos += displace
        return CameraMatrix( t=displace )

    def truck( self, amount ):
        '''Causes the camera to change position by moving the camera in its right direction.
        If the right direction is not perpendicular with the world's up, the camera WILL change elevation.

        Positive values cause the camera to move right, negative left.

        @param:     amount      The amount to move the camera (in meters).
        @returns:   A matrix representing the camera's transformation.
        '''
        displace = self.right * amount
        self.pos += displace
        return CameraMatrix( t=displace )

    def truckPedastal( self, dx, dy ):
        '''Performs a simultaneous truck and pedastal.
        This causes the camera to move on its facing plane.

        @param:     dx      The change in the camera's position along its right axis.
                            Positive values move the camera right, negative move left.
        @param:     dy      The change in the camera's position along its up axis.
                            Positive values move the camera up, negative move down.
        @returns:   A matrix representing the camera's net transformation.
        '''
        displace = self.right * dx + self.up * dy
        self.pos += displace
        return CameraMatrix( t=displace )

    # QUERIES ON THE CAMERA
    def sqDist( self, p ):
        '''Computes the squared distance from the camera to this point.

        @param:     p       The point to test.
        @returns:   A float.  The squared distance from the camera position to this point.
        '''
        return ( self.pos - p ).lengthSq()

    def distance( self, p ):
        '''Computes the  distance from the camera to this point.

        @param:     p       The point to test.
        @returns:   A float.  The squared distance from the camera position to this point.
        '''
        return ( self.pos - p ).length()

    def eyespace( self, p ):
        '''Returns the eye-space coordinate of the given point.

        @param:     p       The point to transform (defined in world space).
        @returns:   A Vector3 representing the point in eye space.
        '''
        p = p - self.pos
        return self.eyespaceV( p )

    def eyespaceV( self, v ):
        '''Returns the eye-space value of the given *vector*.

        @param:     v       A vector in some direction.
        @returns:   A new Vector3 which is the direction in eyespace.
        '''
        x = v.dot( self.right )
        y = v.dot( self.up )
        z = v.dot( self.facing )
        return Vector3( x, y, z )
    

class GLCamera( Camera ):
    ORTHO = 0
    PERSP = 1
    '''A special camera that connects the logical camera to the OpenGL context'''
    def __init__( self, pos=Vector3(0.0,0.0,0.0), facing=DEF_FACING, up=WORLD_UP, fov=45.0 ):
        Camera.__init__( self, pos, facing, up, fov )
        # the distance of the far plane
        self.nearPlane = 0.05
        self.farPlane = 30.0
        
        # The projection type
        self.projType = GLCamera.PERSP
        # the size of a pixel in world coords (in ortho view) - defaults to 1 m per pixel
        self.pixelScale = 1.0
        
        # size of window this camera draws to (intege value of width and height)
        #   The width and height of the logical orthographic view volume cross section
        self.oWidth = -1
        self.oHeight = -1

    def setFrom( self, camera ):
        '''Sets this camera's attributes from the given camera.

        @param:     camera      An instance of a GLCamera.
        '''
        self.nearPlane = camera.nearPlane
        self.farPlane = camera.farPlane
        self.projType = camera.projType
        self.pixelScale = camera.pixelScale
        self.oWidth = camera.oWidth
        self.oHeight = camera.oHeight
        Camera.setFrom( self, camera )

    def copy( self ):
        '''Returns a copy of this camera.

        @returns:       A new GLCamera instance with this camera's properties set.
        '''
        return deepcopy( self )

    def zoom( self, amount, center=None ):
        '''Changes the "zoom" of the camera.

        If the camera is using a perspective projection, it uses the Camera.zoom functionality.
        If orthographic, it uses custom functionality.

        @param:     amount      The amount of zoom.  If orthographic projection, the amount is a
                                *percentage change* on the current pixel scale.
                                If perspective projection see Camera.zoom for interpretation.
        @param:     center      An optional argument, only used for orthographic projection.
                                The center around which the zoom happens.  If not provided it
                                zooms around the center of the screen.  The value should be in WORLD
                                coordinates.
        '''
        if ( self.projType == self.ORTHO ):
            # TODO: The proper behavior:
            #   the idea is that there is a parallel piped centered on the camera
            #   The user "zooms" around a point.
            #       - The cross-section of the piped perpendicular to the camera facing direction
            #           scales (smaller for zooming in, larger for zooming out).
            #       - if not centered on the camera position, the camera should move so that the
            #           zooming point's projection onto the screen is unchanged.
            #   In other words, if I were to scale the up and right components of the camera's frent
            #       frame to be the old view width and height, I can compute a coordinate for the
            #       center of zoom which would lie in the domain [-1,1]x[-1,1].
            #       Then, when I scale the size of the domain, I should make sure that I displace
            #       the camera along its right/up directions so that the zoom origin has the same
            #       coordinate in the new basis (this will guarantee that it is in the same place
            #       on the screen.
            halfW = self.oWidth * 0.5 * self.pixelScale
            halfH = self.oHeight * 0.5 * self.pixelScale
            localCenter = center - self.pos
            # the old canonical screen space coordinate of the zoom origin
            canonX = localCenter.dot( self.right )
            screenX = canonX / halfW
            canonY = localCenter.dot( self.up )
            screenY = canonY / halfH
            self.pixelScale *= 1.0 + amount
            viewScale = 1.0 / ( 1.0 + amount )
            self.oWidth *= viewScale
            self.oHeight *= viewScale
            if ( screenX != 0.0 ):
                # all points, except the origin, will change screen position due to zooming
                self.pos -= self.right * ( screenX * amount )
            if ( screenY != 0.0 ):
                self.pos -= self.up * ( screenY * amount )
            
            return True
        else:
            return Camera.zoom( self, amount )
            
        
    def setOrtho( self ):
        '''Sets the camera to orthogonal'''
        self.projType = GLCamera.ORTHO

    def setPersp( self ):
        '''Sets the camera to perspective'''
        self.projType = GLCamera.PERSP

    def setProjection( self, w, h ):
        '''Sets the opengl projection matrix.

        @param:     w       The viewport width (the dimension, in pixels, of the screen)
        @param:     h       The viewport height (the dimension, in pixels, of the screen)
        '''
        if ( self.oWidth < 0 ):
            self.oWidth = w
            self.oHeight = h
        glViewport( 0,0,w,h )   #TODO: Change this to accept arbitrary viewports
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity()
        self._setProjMat( w, h )

    def _setProjMat( self, w, h ):
        '''Sets the opengl projection matrix.

        @param:     w       The viewport width (the dimension, in pixels, of the screen)
        @param:     h       The viewport height (the dimension, in pixels, of the screen)
        '''
        if ( self.projType == GLCamera.PERSP ):
            gluPerspective( self.fov, float(w)/float( h ), self.nearPlane, self.farPlane )
        elif ( self.projType == GLCamera.ORTHO ):
            halfW = self.oWidth * 0.5 * self.pixelScale
            halfH = self.oHeight * 0.5 * self.pixelScale
            glOrtho( -halfW, halfW, -halfH, halfH, self.nearPlane, self.farPlane )
        else:
            raise AttributeError, "Invalid projection type for GLCamera: {0}".format( self.projType )
        glMatrixMode( GL_MODELVIEW )

    def setGLView( self ):
        glLoadIdentity()
        tgt = self.pos + self.facing
        gluLookAt( self.pos.x, self.pos.y, self.pos.z,
                   tgt.x, tgt.y, tgt.z,
                   self.up.x, self.up.y, self.up.z )

    def setSelectMat( self, selectPoint, w, h, pickSize=5 ):
        '''Given the selection point, computes the projection matrices for the
        selection matrix.

        @param:     selectPoint     The point, in screen space, at which the selection is occuring.
        @param:     w               The viewport width.
        @param:     h               The viewport height.
        @param:     pickSize        The size of the box that selectables will be considered.
        '''
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity()
        viewport = ( 0, 0, w, h )
        gluPickMatrix( selectPoint[0], h - selectPoint[1], pickSize, pickSize, viewport )
        self._setProjMat( w, h )

    def setSelectMatRegion( self, x0, y0, x1, y1, w, h ):
        '''Given the selection point, computes the projection matrices for the
        selection matrix.

        @param:     x0          The minimum x-value of the rectangular region.
        @param:     y0          The minimum y-value of the rectangular region.
        @param:     x1          The maximum x-value of the rectangular region.
        @param:     y1          The amximum y-value of the rectangular region.
        @param:     w               The viewport width.
        @param:     h               The viewport height.
        '''
        dx = abs( x1 - x0 ) 
        dy = abs( y1 - y0 )
        x = ( x0 + x1 ) * 0.5
        y = ( y0 + y1 ) * 0.5
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity()
        viewport = ( 0, 0, w, h )
        gluPickMatrix( x, y, dx, dy, viewport )
        self._setProjMat( w, h )

if __name__ == '__main__':
    cam = Camera()
    print cam
