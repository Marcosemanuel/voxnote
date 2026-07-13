import QtQuick
import QtQuick.Controls
import ".."

TextArea {
    id: control

    leftPadding: 14
    rightPadding: 14
    topPadding: 12
    bottomPadding: 12
    color: Theme.text
    placeholderTextColor: "#8A919E"
    selectionColor: Theme.primary
    selectedTextColor: "#FFFFFF"
    font.family: "Manrope"
    font.pixelSize: 16
    font.weight: Font.Normal
    wrapMode: TextEdit.Wrap

    background: Rectangle {
        radius: Theme.radiusSmall
        color: Theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.primary : Theme.line
    }
}
