import QtQuick
import QtQuick.Controls
import ".."

ComboBox {
    id: control
    implicitHeight: 52
    leftPadding: 16
    rightPadding: 42
    font.family: "Manrope"
    font.pixelSize: 16
    font.weight: Font.Normal

    contentItem: Text {
        leftPadding: 0
        text: control.displayText
        color: Theme.ink
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        font: control.font
    }

    background: Rectangle {
        radius: Theme.radiusSmall
        color: Theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.primary : Theme.line
    }

    indicator: Text {
        x: control.width - width - 17
        y: (control.height - height) / 2 - 1
        text: "\u2304"
        color: Theme.text
        font.family: "Segoe UI Symbol"
        font.pixelSize: 18
        font.weight: Font.Medium
    }

    delegate: Rectangle {
        id: option
        required property var modelData
        required property int index
        width: ListView.view ? ListView.view.width : control.width
        height: 42
        radius: 7
        color: optionMouse.containsMouse || control.currentIndex === index ? Theme.primarySoft : Theme.surface

        Text {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            text: String(option.modelData)
            color: "#111111"
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
            font.family: "Manrope"
            font.pixelSize: 14
            font.weight: Font.Normal
        }

        MouseArea {
            id: optionMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                control.currentIndex = option.index;
                control.popup.close();
            }
        }
    }

    popup: Popup {
        y: control.height + 6
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 224)
        padding: 4
        topMargin: 8
        bottomMargin: 8

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }

        background: Rectangle {
            radius: Theme.radiusSmall
            color: Theme.surface
            border.width: 1
            border.color: Theme.line
        }
    }
}
