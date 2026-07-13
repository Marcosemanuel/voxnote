import QtQuick
import QtQuick.Controls
import ".."

ProgressBar {
    id: control

    implicitHeight: 8
    from: 0
    to: 100

    background: Rectangle {
        implicitHeight: 8
        radius: 4
        color: "#E8ECF2"
    }

    contentItem: Item {
        implicitHeight: 8

        Rectangle {
            width: control.indeterminate ? parent.width * 0.34 : Math.max(0, Math.min(parent.width, control.visualPosition * parent.width))
            height: parent.height
            radius: 4
            color: Theme.primary
            x: control.indeterminate ? (parent.width - width) * 0.5 : 0

            Behavior on width {
                NumberAnimation {
                    duration: 180
                }
            }
            Behavior on x {
                NumberAnimation {
                    duration: 600
                    loops: Animation.Infinite
                    running: control.indeterminate
                }
            }
        }
    }
}
