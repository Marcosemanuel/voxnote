import QtQuick
import QtQuick.Controls
import ".."

CheckBox {
    id: control

    implicitHeight: Math.max(24, contentItem.implicitHeight)
    spacing: 10
    hoverEnabled: true
    font.family: "Manrope"
    font.pixelSize: 14
    font.weight: Font.Medium

    indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: 20
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        radius: 6
        color: control.checked ? Theme.primary : Theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.checked || control.activeFocus ? Theme.primary : Theme.line

        Text {
            anchors.centerIn: parent
            text: "\u2713"
            visible: control.checked
            color: "#FFFFFF"
            font.family: "Manrope"
            font.pixelSize: 14
            font.weight: Font.Bold
        }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.text : Theme.muted
        font: control.font
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.Wrap
        leftPadding: control.indicator.width + control.spacing
    }
}
