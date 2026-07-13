import QtQuick
import QtQuick.Controls
import ".."

TextField {
    id: control
    implicitHeight: 52
    leftPadding: 16
    rightPadding: 16
    color: Theme.ink
    placeholderTextColor: "#8A919E"
    selectionColor: Theme.primary
    selectedTextColor: "white"
    font.family: "Manrope"
    font.pixelSize: 16
    font.weight: Font.Normal

    background: Rectangle {
        radius: Theme.radiusSmall
        color: Theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.primary : Theme.line
    }
}
