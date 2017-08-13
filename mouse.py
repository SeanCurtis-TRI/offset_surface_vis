from GuiAPI import QT

if ( QT ):
    from PyQt4 import QtCore, QtGui

    LEFT_BTN = QtCore.Qt.LeftButton
    MIDDLE_BTN = QtCore.Qt.MidButton
    RIGHT_BTN = QtCore.Qt.RightButton
    #TODO: Determine these events (if necessary)
    WHEEL_UP = 4
    WHEEL_DOWN = 5

    CURR_BUTTONS = 0

    def getModState():
        '''Reports the current mod state, booleans reporting:
            1. if ctrl is down
            2. if alt is down
            3. if shift is down
        '''
        mods = QtGui.QApplication.keyboardModifiers()
        hasCtrl = bool( mods & QtCore.Qt.ControlModifier )
        hasAlt = bool( mods & QtCore.Qt.AltModifier )
        hasShift = bool( mods & QtCore.Qt.ShiftModifier )
        return hasCtrl, hasAlt, hasShift

    def buttonDown( btn ):
        '''Infornms the system that a mouse button has been pressed.

        @param:     btn         The identifier of the mouse button that has been pressed.
        '''
        global CURR_BUTTONS
        CURR_BUTTONS |= btn

    def buttonUp( btn ):
        '''Informs the systemt hat a mouse button has been released.

        @param:     btn         The identifier of the mouse button that has been released.
        '''
        global CURR_BUTTONS
        CURR_BUTTONS &= ~btn

    def mouseButtons():
        '''Returns the mouse button state.

        @returns:       An identifier which is a logical or of all pressed mouse buttons.
        '''
        return CURR_BUTTONS
else:
    import pygame
    
    # pygame mouse event button values
    NO_BTN = 0
    LEFT_BTN = 1
    MIDDLE_BTN = 2
    RIGHT_BTN = 3
    WHEEL_UP = 4
    WHEEL_DOWN = 5

    def getModState():
        '''Reports the current mod state, booleans reporting:
            1. if ctrl is down
            2. if alt is down
            3. if shift is down
        '''
        mods = pygame.key.get_mods()
        hasCtrl = mods & pygame.KMOD_CTRL
        hasAlt = mods & pygame.KMOD_ALT
        hasShift = mods & pygame.KMOD_SHIFT
        return hasCtrl, hasAlt, hasShift

