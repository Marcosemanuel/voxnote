import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Button {
    id: control
    property bool active: false
    property bool compact: false
    property url iconSource: ""

    implicitHeight: 56
    hoverEnabled: true
    padding: 0

    contentItem: RowLayout {
        anchors.fill: parent
        anchors.leftMargin: control.compact ? 0 : 18
        anchors.rightMargin: 12
        spacing: 14

        Image {
            source: control.iconSource
            sourceSize.width: 22
            sourceSize.height: 22
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            Layout.alignment: control.compact ? Qt.AlignHCenter : Qt.AlignVCenter
        }

        Text {
            visible: !control.compact
            text: control.text
            color: control.active ? Theme.primaryDark : Theme.text
            font.family: "Manrope"
            font.pixelSize: 14
            font.weight: control.active ? Font.DemiBold : Font.Medium
            Layout.fillWidth: true
        }
    }

    background: Rectangle {
        radius: 12
        color: control.active ? Theme.primarySoft : (control.hovered ? "#F4F6F8" : "transparent")

        Rectangle {
            visible: control.active
            width: 3
            height: 32
            radius: 2
            color: Theme.primary
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
