import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Button {
    id: control
    property bool primary: false
    property bool danger: false
    property bool iconOnly: false
    property url iconSource: ""
    property rect iconCrop: Qt.rect(0, 0, 0, 0)
    readonly property color foregroundColor: primary ? "#FFFFFF" : (danger ? Theme.danger : Theme.primaryDark)
    readonly property color backgroundColor: primary ? (down ? Theme.primaryDark : Theme.primary) : (hovered || down ? Theme.primarySoft : Theme.surface)

    implicitHeight: 46
    implicitWidth: iconOnly ? 46 : Math.max(120, contentRow.implicitWidth + 36)
    padding: 0
    hoverEnabled: true
    font.family: "Manrope"
    font.pixelSize: 14
    font.weight: Font.DemiBold

    contentItem: RowLayout {
        id: contentRow
        anchors.centerIn: parent
        spacing: 9

        Image {
            visible: control.iconSource.toString().length > 0
            source: control.iconSource
            sourceClipRect: control.iconCrop
            Layout.preferredWidth: visible ? 20 : 0
            Layout.preferredHeight: visible ? 20 : 0
            fillMode: Image.PreserveAspectFit
        }

        Text {
            visible: !control.iconOnly && control.text.length > 0
            text: control.text
            color: control.foregroundColor
            font: control.font
        }
    }

    background: Rectangle {
        radius: Theme.radiusSmall
        color: control.backgroundColor
        border.width: control.primary ? 0 : 1
        border.color: control.danger ? "#F0B9B9" : "#A8C7FA"
        opacity: control.enabled ? 1 : 0.48

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
    }
}
