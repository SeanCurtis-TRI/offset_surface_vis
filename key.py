from GuiAPI import QT

if ( QT ):
    from PyQt4 import QtCore
    LEFT_BRACKET = QtCore.Qt.Key_BracketLeft
    RIGHT_BRACKET = QtCore.Qt.Key_BracketRight
    K_f = QtCore.Qt.Key_F
    K_a = QtCore.Qt.Key_A
    K_p = QtCore.Qt.Key_P
else:
    LEFT_BRACKET = 2