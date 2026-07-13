pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtMultimedia
import "."

ApplicationWindow {
    id: root
    width: 1280
    height: 820
    minimumWidth: 980
    minimumHeight: 680
    visible: true
    title: "Voxnote"
    color: Theme.canvas
    palette.accent: Theme.primary

    readonly property bool compactNav: width < 1160
    readonly property int pagePadding: width < 1160 ? 28 : 46
    readonly property string icons: backend.assetRoot + "/icons/lucide/"
    readonly property string uiAssets: backend.assetRoot + "/ui/"
    property bool closeApproved: false
    property int exportJobId: 0
    property int exportMeetingSessionId: 0
    property int exportMeetingRunId: 0

    Component.onCompleted: backend.start_update_check()

    onClosing: function (close) {
        if (closeApproved) {
            close.accepted = true;
            return;
        }
        close.accepted = false;
        backend.request_close();
    }

    FileDialog {
        id: audioDialog
        title: "Selecionar áudios"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["Áudios (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus *.wma *.aiff *.aif *.webm)"]
        onAccepted: backend.add_files(selectedFiles)
    }

    FileDialog {
        id: exportDialog
        title: "Exportar transcrição"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Texto (*.txt)", "Legendas SRT (*.srt)", "Legendas WebVTT (*.vtt)", "Dados JSON (*.json)"]
        onAccepted: backend.export_job(root.exportJobId, selectedFile.toString(), selectedNameFilter)
    }

    FileDialog {
        id: meetingExportDialog
        title: "Exportar reunião"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Texto (*.txt)", "Legendas SRT (*.srt)", "Legendas WebVTT (*.vtt)", "Dados JSON (*.json)"]
        onAccepted: backend.export_meeting_run(root.exportMeetingSessionId, root.exportMeetingRunId, selectedFile.toString(), selectedNameFilter)
    }

    Dialog {
        id: noticeDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 440
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        property string heading: ""
        property string body: ""
        property string level: "info"

        background: Rectangle {
            radius: Theme.radius
            color: Theme.surface
            border.width: 1
            border.color: Theme.line
        }
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: noticeDialog.heading
                color: Theme.ink
                font.family: "Manrope"
                font.pixelSize: 20
                font.weight: Font.DemiBold
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }
            Label {
                text: noticeDialog.body
                color: Theme.text
                font.family: "Manrope"
                font.pixelSize: 14
                lineHeight: 1.45
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
        footer: Item {
            implicitHeight: 70
            VxButton {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 20
                text: "Entendi"
                primary: true
                onClicked: noticeDialog.close()
            }
        }
    }

    Dialog {
        id: confirmationDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 440
        modal: true
        closePolicy: Popup.NoAutoClose
        property string action: ""
        property string heading: ""
        property string body: ""

        background: Rectangle {
            radius: Theme.radius
            color: Theme.surface
            border.width: 1
            border.color: Theme.line
        }
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: confirmationDialog.heading
                color: Theme.ink
                font.family: "Manrope"
                font.pixelSize: 20
                font.weight: Font.DemiBold
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }
            Label {
                text: confirmationDialog.body
                color: Theme.text
                font.family: "Manrope"
                font.pixelSize: 14
                lineHeight: 1.45
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
        footer: Item {
            implicitHeight: 70
            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 20
                spacing: 10
                VxButton {
                    text: "Cancelar"
                    onClicked: {
                        backend.reject_confirmation();
                        confirmationDialog.close();
                    }
                }
                VxButton {
                    text: confirmationDialog.action === "delete" || confirmationDialog.action === "remove_model" ? "Remover" : "Confirmar"
                    primary: confirmationDialog.action !== "delete" && confirmationDialog.action !== "remove_model"
                    danger: confirmationDialog.action === "delete" || confirmationDialog.action === "remove_model"
                    onClicked: {
                        backend.confirm(confirmationDialog.action);
                        confirmationDialog.close();
                    }
                }
            }
        }
    }

    Connections {
        target: backend
        function onNoticeRequested(level, heading, body) {
            noticeDialog.level = level;
            noticeDialog.heading = heading;
            noticeDialog.body = body;
            noticeDialog.open();
        }
        function onConfirmationRequested(action, heading, body) {
            confirmationDialog.action = action;
            confirmationDialog.heading = heading;
            confirmationDialog.body = body;
            confirmationDialog.open();
        }
        function onCloseRequested() {
            root.closeApproved = true;
            root.close();
        }
    }

    Rectangle {
        id: updateBanner
        visible: backend.updateAvailable
        z: 100
        width: Math.min(440, root.width - 40)
        height: updateContent.implicitHeight + 32
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 20
        anchors.rightMargin: 20
        radius: Theme.radius
        color: Theme.surface
        border.width: 1
        border.color: "#A8C7FA"

        RowLayout {
            id: updateContent
            anchors.fill: parent
            anchors.margins: 16
            spacing: 14
            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 18
                color: Theme.primarySoft
                Text {
                    anchors.centerIn: parent
                    text: "↑"
                    color: Theme.primaryDark
                    font.family: "Manrope"
                    font.pixelSize: 20
                    font.weight: Font.Bold
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Atualização disponível"
                    color: Theme.ink
                    font.family: "Manrope"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
                Text {
                    text: "Versão " + backend.updateVersion + " pronta para baixar."
                    color: Theme.text
                    font.family: "Manrope"
                    font.pixelSize: 12
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
            VxButton {
                text: "Ver atualização"
                primary: true
                Layout.preferredWidth: 144
                onClicked: Qt.openUrlExternally(backend.updateUrl)
            }
        }
    }

    function openExport(jobId) {
        root.exportJobId = jobId;
        exportDialog.currentFile = backend.default_export_path(jobId);
        exportDialog.open();
    }

    function openMeetingExport(sessionId, runId) {
        root.exportMeetingSessionId = sessionId;
        root.exportMeetingRunId = runId;
        meetingExportDialog.currentFile = backend.default_meeting_export_path(sessionId);
        meetingExportDialog.open();
    }

    component PageTitle: Text {
        color: Theme.ink
        font.family: "Manrope"
        font.pixelSize: 32
        font.weight: Font.Bold
        lineHeight: 1.25
    }

    component SectionTitle: Text {
        color: Theme.ink
        font.family: "Manrope"
        font.pixelSize: 20
        font.weight: Font.DemiBold
        lineHeight: 1.4
    }

    component BodyText: Text {
        color: Theme.text
        font.family: "Manrope"
        font.pixelSize: 16
        font.weight: Font.Normal
        lineHeight: 1.5
    }

    component CaptionText: Text {
        color: Theme.muted
        font.family: "Manrope"
        font.pixelSize: 13
        font.weight: Font.Medium
        lineHeight: 1.4
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: sidebar
            Layout.preferredWidth: root.compactNav ? 82 : 258
            Layout.minimumWidth: Layout.preferredWidth
            Layout.maximumWidth: Layout.preferredWidth
            Layout.fillHeight: true
            color: "#FBFAF8"
            border.width: 1
            border.color: Theme.line

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 88

                    RowLayout {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: root.compactNav ? 7 : 12
                        spacing: 10

                        Image {
                            source: backend.assetRoot + "/branding/voxnote-symbol.png"
                            sourceSize.width: 42
                            sourceSize.height: 42
                            Layout.preferredWidth: 42
                            Layout.preferredHeight: 42
                            fillMode: Image.PreserveAspectFit
                        }

                        Text {
                            visible: !root.compactNav
                            text: "Voxnote"
                            color: Theme.ink
                            font.family: "Manrope"
                            font.pixelSize: 21
                            font.weight: Font.Bold
                        }
                    }
                }

                Repeater {
                    model: [
                        {
                            label: "Nova transcrição",
                            icon: "mic.svg",
                            page: 0
                        },
                        {
                            label: "Capturar reunião",
                            icon: "audio-lines.svg",
                            page: 7
                        },
                        {
                            label: "Transcrições",
                            icon: "file-text.svg",
                            page: 1
                        },
                        {
                            label: "Modelos",
                            icon: "notebook-pen.svg",
                            page: 2
                        },
                        {
                            label: "Configurações",
                            icon: "sparkles.svg",
                            page: 3
                        },
                        {
                            label: "Ajuda",
                            icon: "notebook-pen.svg",
                            page: 4
                        }
                    ]

                    NavItem {
                        required property var modelData
                        Layout.fillWidth: true
                        text: modelData.label
                        iconSource: root.icons + modelData.icon
                        active: backend.page === modelData.page
                        compact: root.compactNav
                        Accessible.name: text
                        onClicked: backend.navigate(modelData.page)
                    }
                }

                Item {
                    Layout.fillHeight: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.compactNav ? 62 : 142
                    radius: 14
                    color: Theme.surface
                    border.width: 1
                    border.color: Theme.line

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: root.compactNav ? 10 : 16
                        spacing: 8

                        Image {
                            source: root.uiAssets + "hardware.png"
                            sourceClipRect: Qt.rect(16, 20, 24, 22)
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                            Layout.alignment: root.compactNav ? Qt.AlignHCenter : Qt.AlignLeft
                        }

                        Text {
                            visible: !root.compactNav
                            text: "Hardware disponível"
                            color: Theme.ink
                            font.family: "Manrope"
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                        }

                        CaptionText {
                            visible: !root.compactNav
                            text: backend.hardwareSummary
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        StackLayout {
            id: pages
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: backend.page

            // Nova transcrição
            Item {
                ScrollView {
                    id: newScroll
                    anchors.fill: parent
                    contentWidth: availableWidth
                    clip: true

                    ColumnLayout {
                        x: root.pagePadding
                        width: Math.max(0, newScroll.availableWidth - root.pagePadding * 2)
                        spacing: 18

                        Item {
                            Layout.preferredHeight: 12
                        }

                        PageTitle {
                            text: "Nova transcrição"
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 248
                            color: Theme.surface
                            radius: Theme.radiusLarge
                            border.width: 1
                            border.color: Theme.line

                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 18
                                color: "transparent"
                                radius: 16
                                border.width: 2
                                border.color: "#9BBEF8"

                                DropArea {
                                    anchors.fill: parent
                                    onDropped: function (drop) {
                                        if (drop.hasUrls)
                                            backend.add_files(drop.urls);
                                    }
                                }

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: 8

                                    Image {
                                        source: root.icons + "audio-lines.svg"
                                        sourceSize.width: 44
                                        sourceSize.height: 44
                                        Layout.preferredWidth: 44
                                        Layout.preferredHeight: 44
                                        Layout.alignment: Qt.AlignHCenter
                                    }
                                    SectionTitle {
                                        text: "Arraste seus arquivos de áudio aqui"
                                        horizontalAlignment: Text.AlignHCenter
                                        Layout.alignment: Qt.AlignHCenter
                                    }
                                    CaptionText {
                                        text: "ou use o botão abaixo"
                                        Layout.alignment: Qt.AlignHCenter
                                    }
                                    VxButton {
                                        text: "Selecionar arquivos"
                                        primary: true
                                        iconSource: root.icons + "file-text.svg"
                                        Layout.alignment: Qt.AlignHCenter
                                        onClicked: audioDialog.open()
                                    }
                                    CaptionText {
                                        text: "MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF e WEBM"
                                        Layout.alignment: Qt.AlignHCenter
                                    }
                                }
                            }
                        }

                        Rectangle {
                            visible: backend.files.length > 0
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(160, fileColumn.implicitHeight + 24)
                            radius: Theme.radius
                            color: Theme.surface
                            border.width: 1
                            border.color: Theme.line

                            ColumnLayout {
                                id: fileColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 4

                                Repeater {
                                    model: backend.files
                                    delegate: RowLayout {
                                        required property var modelData
                                        required property int index
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 42
                                        spacing: 10

                                        Image {
                                            source: root.icons + "file-text.svg"
                                            sourceSize.width: 20
                                            sourceSize.height: 20
                                            Layout.preferredWidth: 20
                                            Layout.preferredHeight: 20
                                        }
                                        CaptionText {
                                            text: modelData.name
                                            color: Theme.text
                                            elide: Text.ElideMiddle
                                            Layout.fillWidth: true
                                        }
                                        CaptionText {
                                            text: modelData.duration + " • " + modelData.format + " • " + modelData.size
                                        }
                                        VxButton {
                                            iconOnly: true
                                            danger: true
                                            iconSource: root.uiAssets + "action-delete.png"
                                            Accessible.name: "Remover arquivo"
                                            onClicked: backend.remove_file(index)
                                        }
                                    }
                                }
                            }
                        }

                        SectionTitle {
                            text: "Configurações"
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: width < 760 ? 1 : 2
                            columnSpacing: 24
                            rowSpacing: 14

                            CaptionText {
                                text: "Idioma"
                                color: Theme.ink
                            }
                            VxComboBox {
                                id: language
                                Layout.fillWidth: true
                                Layout.preferredHeight: 48
                                model: ["Português (Brasil)", "Detectar automaticamente", "Inglês", "Espanhol"]
                            }
                            CaptionText {
                                text: "Qualidade"
                                color: Theme.ink
                            }
                            VxComboBox {
                                id: quality
                                Layout.fillWidth: true
                                Layout.preferredHeight: 48
                                model: ["Leve", "Equilibrada", "Alta precisão", "Rápida"]
                                Component.onCompleted: currentIndex = Math.max(0, model.indexOf(backend.recommendedProfile))
                            }
                            CaptionText {
                                text: "Glossário"
                                color: Theme.ink
                                Layout.alignment: Qt.AlignTop
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 76
                                radius: Theme.radiusSmall
                                color: Theme.surface
                                border.width: glossary.activeFocus ? 2 : 1
                                border.color: glossary.activeFocus ? Theme.primary : Theme.line

                                TextArea {
                                    id: glossary
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    placeholderText: "Nomes, siglas e termos técnicos — um por linha (opcional)"
                                    wrapMode: TextEdit.Wrap
                                    color: Theme.ink
                                    placeholderTextColor: "#8A919E"
                                    background: null
                                    font.family: "Manrope"
                                    font.pixelSize: 16
                                }
                            }
                        }

                        CaptionText {
                            text: backend.hardwareRecommendation
                            color: Theme.success
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: Theme.line
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            CaptionText {
                                text: "Processamento local. O áudio não é enviado para a internet."
                                Layout.fillWidth: true
                                wrapMode: Text.Wrap
                            }
                            VxButton {
                                text: "Iniciar transcrição"
                                primary: true
                                enabled: backend.files.length > 0
                                onClicked: {
                                    const languageMap = ["pt", "auto", "en", "es"];
                                    backend.start_queue(languageMap[language.currentIndex], quality.currentText, glossary.text);
                                }
                            }
                        }

                        Item {
                            Layout.preferredHeight: 8
                        }
                    }
                }
            }

            // Transcrições
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: root.pagePadding
                    anchors.rightMargin: root.pagePadding
                    anchors.topMargin: 34
                    anchors.bottomMargin: 30
                    spacing: 22

                    RowLayout {
                        Layout.fillWidth: true
                        PageTitle {
                            text: "Transcrições"
                            Layout.fillWidth: true
                        }
                        VxField {
                            Layout.preferredWidth: 340
                            Layout.maximumWidth: 340
                            placeholderText: "Buscar por nome..."
                            onTextChanged: backend.search_jobs(text)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Theme.radiusLarge
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.line
                        clip: true

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 58
                                Layout.leftMargin: 18
                                Layout.rightMargin: 18
                                CaptionText {
                                    text: "Arquivo"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 4
                                }
                                CaptionText {
                                    text: "Duração"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1
                                }
                                CaptionText {
                                    text: "Estado"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1.2
                                }
                                CaptionText {
                                    text: "Progresso"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1.2
                                }
                                CaptionText {
                                    text: "Ações"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.preferredWidth: 156
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: Theme.line
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: backend.jobs

                                delegate: ColumnLayout {
                                    required property var modelData
                                    width: ListView.view.width
                                    spacing: 0

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 66
                                        Layout.leftMargin: 18
                                        Layout.rightMargin: 18
                                        spacing: 12

                                        RowLayout {
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 4
                                            spacing: 10
                                            Image {
                                                source: root.icons + "file-text.svg"
                                                sourceSize.width: 21
                                                sourceSize.height: 21
                                                Layout.preferredWidth: 21
                                                Layout.preferredHeight: 21
                                            }
                                            CaptionText {
                                                text: modelData.name
                                                color: Theme.text
                                                elide: Text.ElideMiddle
                                                Layout.fillWidth: true
                                            }
                                        }
                                        CaptionText {
                                            text: modelData.duration
                                            color: Theme.text
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 1
                                        }
                                        CaptionText {
                                            text: modelData.status
                                            color: modelData.statusKey === "completed" ? Theme.success : Theme.text
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 1.2
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 1.2
                                            spacing: 4
                                            CaptionText {
                                                text: modelData.progress.toFixed(1) + "%"
                                                color: Theme.text
                                            }
                                            ProgressBar {
                                                from: 0
                                                to: 100
                                                value: modelData.progress
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 4
                                            }
                                        }
                                        RowLayout {
                                            Layout.preferredWidth: 156
                                            spacing: 6
                                            VxButton {
                                                iconOnly: true
                                                iconSource: root.uiAssets + "action-open.png"
                                                iconCrop: Qt.rect(15, 17, 17, 12)
                                                Accessible.name: modelData.canContinue ? "Continuar" : "Abrir"
                                                onClicked: modelData.canContinue ? backend.resume_job(modelData.id) : backend.open_job(modelData.id)
                                            }
                                            VxButton {
                                                iconOnly: true
                                                iconSource: root.uiAssets + "action-export.png"
                                                iconCrop: Qt.rect(17, 15, 14, 16)
                                                Accessible.name: "Exportar"
                                                onClicked: root.openExport(modelData.id)
                                            }
                                            VxButton {
                                                iconOnly: true
                                                danger: true
                                                iconSource: root.uiAssets + "action-delete.png"
                                                iconCrop: Qt.rect(16, 16, 14, 14)
                                                Accessible.name: "Excluir"
                                                onClicked: backend.request_delete_job(modelData.id)
                                            }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 1
                                        color: Theme.line
                                    }
                                }

                                ScrollBar.vertical: ScrollBar {}
                            }
                        }
                    }
                }
            }

            // Modelos
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: root.pagePadding
                    anchors.rightMargin: root.pagePadding
                    anchors.topMargin: 34
                    anchors.bottomMargin: 30
                    spacing: 12

                    PageTitle {
                        text: "Modelos"
                    }
                    BodyText {
                        text: "Baixe os modelos antes de transcrever ou deixe o aplicativo baixá-los automaticamente."
                        color: Theme.muted
                        Layout.bottomMargin: 14
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Theme.radiusLarge
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.line
                        clip: true

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 58
                                Layout.leftMargin: 22
                                Layout.rightMargin: 22
                                CaptionText {
                                    text: "Perfil"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 3
                                }
                                CaptionText {
                                    text: "Modelo"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1.5
                                }
                                CaptionText {
                                    text: "Estado"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: 1.5
                                }
                                CaptionText {
                                    text: "Ação"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                    Layout.preferredWidth: 132
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: Theme.line
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: backend.models
                                delegate: ColumnLayout {
                                    required property var modelData
                                    width: ListView.view.width
                                    spacing: 0
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 72
                                        Layout.leftMargin: 22
                                        Layout.rightMargin: 22
                                        CaptionText {
                                            text: modelData.label
                                            color: Theme.text
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 3
                                        }
                                        CaptionText {
                                            text: modelData.name
                                            color: Theme.text
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 1.5
                                        }
                                        CaptionText {
                                            text: modelData.status + (modelData.size ? " • " + modelData.size : "")
                                            color: modelData.installed ? Theme.success : Theme.text
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 1.5
                                        }
                                        VxButton {
                                            Layout.preferredWidth: 132
                                            text: modelData.installed ? "Remover" : "Baixar"
                                            danger: modelData.installed
                                            iconSource: modelData.installed ? root.uiAssets + "action-delete.png" : root.uiAssets + "action-export.png"
                                            iconCrop: modelData.installed ? Qt.rect(16, 16, 14, 14) : Qt.rect(17, 15, 14, 16)
                                            onClicked: backend.request_model_action(modelData.name, modelData.installed)
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 1
                                        color: Theme.line
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Configurações
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: root.pagePadding
                    anchors.rightMargin: root.pagePadding
                    anchors.topMargin: 34
                    anchors.bottomMargin: 30
                    spacing: 22
                    PageTitle {
                        text: "Configurações"
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 430
                        radius: Theme.radiusLarge
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.line

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 32
                            spacing: 18
                            RowLayout {
                                spacing: 14
                                Rectangle {
                                    Layout.preferredWidth: 48
                                    Layout.preferredHeight: 48
                                    radius: 24
                                    color: Theme.primarySoft
                                    Image {
                                        anchors.centerIn: parent
                                        source: root.icons + "sparkles.svg"
                                        sourceSize.width: 26
                                        sourceSize.height: 26
                                    }
                                }
                                SectionTitle {
                                    text: "Configuração automática ativa"
                                }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 28
                                rowSpacing: 16
                                CaptionText {
                                    text: "Processador:"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                }
                                BodyText {
                                    text: backend.processor
                                    Layout.fillWidth: true
                                    wrapMode: Text.Wrap
                                }
                                CaptionText {
                                    text: "Processadores lógicos:"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                }
                                BodyText {
                                    text: backend.logicalProcessors
                                }
                                CaptionText {
                                    text: "Memória:"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                }
                                BodyText {
                                    text: backend.memory
                                }
                                CaptionText {
                                    text: "Aceleração:"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                }
                                BodyText {
                                    text: backend.acceleration
                                    wrapMode: Text.Wrap
                                }
                                CaptionText {
                                    text: "Recomendação:"
                                    color: Theme.ink
                                    font.weight: Font.DemiBold
                                }
                                BodyText {
                                    text: backend.recommendedProfile
                                    color: Theme.primaryDark
                                    font.weight: Font.DemiBold
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: Theme.line
                            }
                            RowLayout {
                                spacing: 14
                                Image {
                                    source: root.icons + "mic.svg"
                                    sourceSize.width: 24
                                    sourceSize.height: 24
                                    Layout.preferredWidth: 24
                                    Layout.preferredHeight: 24
                                }
                                BodyText {
                                    text: "O processamento é local. Falhas de aceleração NVIDIA retornam automaticamente para CPU."
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }

            // Ajuda
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: root.pagePadding
                    anchors.rightMargin: root.pagePadding
                    anchors.topMargin: 34
                    anchors.bottomMargin: 30
                    spacing: 22
                    PageTitle {
                        text: "Ajuda"
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Theme.radiusLarge
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.line

                        ScrollView {
                            anchors.fill: parent
                            anchors.margins: 30
                            contentWidth: availableWidth
                            ColumnLayout {
                                width: parent.width
                                spacing: 22
                                Repeater {
                                    model: [
                                        {
                                            title: "Como usar",
                                            body: "1. Abra Nova transcrição.\n2. Selecione os áudios.\n3. Confirme idioma e qualidade.\n4. Inicie e aguarde o download do modelo.\n5. Revise e exporte.",
                                            icon: "notebook-pen.svg"
                                        },
                                        {
                                            title: "Como melhorar a precisão",
                                            body: "Informe o idioma, use Alta precisão quando o computador permitir e revise os trechos marcados.",
                                            icon: "sparkles.svg"
                                        },
                                        {
                                            title: "Privacidade",
                                            body: "O áudio é processado localmente e não é enviado para um serviço de transcrição.",
                                            icon: "mic.svg"
                                        },
                                        {
                                            title: "Formatos",
                                            body: "MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF e WEBM.",
                                            icon: "file-text.svg"
                                        }
                                    ]
                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 12
                                        RowLayout {
                                            spacing: 14
                                            Rectangle {
                                                Layout.preferredWidth: 48
                                                Layout.preferredHeight: 48
                                                radius: 24
                                                color: Theme.primarySoft
                                                Image {
                                                    anchors.centerIn: parent
                                                    source: root.icons + modelData.icon
                                                    sourceSize.width: 25
                                                    sourceSize.height: 25
                                                }
                                            }
                                            SectionTitle {
                                                text: modelData.title
                                            }
                                        }
                                        BodyText {
                                            text: modelData.body
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                            Layout.leftMargin: 62
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 1
                                            color: Theme.line
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Progresso
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: root.pagePadding
                    spacing: 22
                    PageTitle {
                        text: "Transcrição em andamento"
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 360
                        radius: Theme.radiusLarge
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.line
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 32
                            spacing: 18
                            SectionTitle {
                                text: backend.progressTitle
                                Layout.fillWidth: true
                                elide: Text.ElideMiddle
                            }
                            CaptionText {
                                text: backend.progressDetail
                            }
                            ProgressBar {
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: backend.progressValue
                            }
                            BodyText {
                                text: backend.progressValue.toFixed(1) + "% processado"
                                color: Theme.primaryDark
                                font.weight: Font.DemiBold
                            }
                            CaptionText {
                                text: backend.progressLatest
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                            Item {
                                Layout.fillHeight: true
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Item {
                                    Layout.fillWidth: true
                                }
                                VxButton {
                                    text: "Pausar / continuar"
                                    onClicked: backend.toggle_pause()
                                }
                                VxButton {
                                    text: "Cancelar"
                                    danger: true
                                    onClicked: backend.request_cancel_current()
                                }
                            }
                        }
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }

            // Revisão
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: root.pagePadding
                    spacing: 18
                    RowLayout {
                        Layout.fillWidth: true
                        PageTitle {
                            text: backend.reviewTitle
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                        }
                        VxButton {
                            text: "Voltar"
                            onClicked: backend.navigate(1)
                        }
                        VxButton {
                            text: "Exportar"
                            primary: true
                            onClicked: root.openExport(backend.reviewJobId)
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 70
                        radius: Theme.radius
                        color: Theme.surface
                        border.width: 1
                        border.color: Theme.line
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            MediaPlayer {
                                id: player
                                source: backend.reviewAudioUrl
                                audioOutput: AudioOutput {}
                            }
                            VxButton {
                                text: player.playbackState === MediaPlayer.PlayingState ? "Pausar" : "Reproduzir"
                                onClicked: player.playbackState === MediaPlayer.PlayingState ? player.pause() : player.play()
                            }
                            Slider {
                                Layout.fillWidth: true
                                from: 0
                                to: Math.max(1, player.duration)
                                value: player.position
                                onMoved: player.position = value
                            }
                        }
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 10
                        model: backend.reviewSegments
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: Math.max(94, edit.implicitHeight + 32)
                            radius: Theme.radius
                            color: Theme.surface
                            border.width: 1
                            border.color: modelData.attention ? "#F2C66D" : Theme.line
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 14
                                CaptionText {
                                    text: modelData.time
                                    Layout.preferredWidth: 150
                                    color: Theme.muted
                                }
                                TextArea {
                                    id: edit
                                    text: modelData.text
                                    wrapMode: TextEdit.Wrap
                                    Layout.fillWidth: true
                                    background: null
                                    color: Theme.text
                                    font.family: "Manrope"
                                    font.pixelSize: 16
                                    onEditingFinished: backend.revise_segment(modelData.id, text)
                                }
                                CaptionText {
                                    text: modelData.attention ? "Verifique" : "Normal"
                                    color: modelData.attention ? "#9A6500" : Theme.success
                                    Layout.preferredWidth: 82
                                }
                            }
                        }
                    }
                }
            }

            // Captura local de reunião
            Item {
                ScrollView {
                    id: meetingScroll
                    anchors.fill: parent
                    contentWidth: availableWidth
                    clip: true

                    ColumnLayout {
                        x: root.pagePadding
                        width: Math.max(0, meetingScroll.availableWidth - root.pagePadding * 2)
                        spacing: 18

                        Item { Layout.preferredHeight: 12 }
                        PageTitle { text: "Capturar reunião" }
                        BodyText {
                            text: "Capture o áudio reproduzido no Windows e, se quiser, seu microfone. O processamento é local."
                            color: Theme.muted
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: meetingSetup.implicitHeight + 48
                            radius: Theme.radiusLarge
                            color: Theme.surface
                            border.width: 1
                            border.color: Theme.line
                            visible: backend.meetingState === "idle" || backend.meetingState === "failed" || backend.meetingState === "completed"

                            ColumnLayout {
                                id: meetingSetup
                                anchors.fill: parent
                                anchors.margins: 24
                                spacing: 18

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 12
                                    Rectangle {
                                        Layout.preferredWidth: 40
                                        Layout.preferredHeight: 40
                                        radius: 20
                                        color: Theme.primarySoft
                                        Text { anchors.centerIn: parent; text: "1"; color: Theme.primaryDark; font.family: "Manrope"; font.pixelSize: 16; font.weight: Font.Bold }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 2
                                        SectionTitle { text: "Preparar captura" }
                                        CaptionText { text: "Selecione as fontes de áudio, teste o sinal e confirme a autorização."; Layout.fillWidth: true; wrapMode: Text.Wrap }
                                    }
                                }

                                VxCheckBox {
                                    id: captureConsent
                                    text: "Confirmo que tenho autorização para gravar esta reunião."
                                    checked: false
                                    Layout.fillWidth: true
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: width < 760 ? 1 : 2
                                    columnSpacing: 18
                                    rowSpacing: 14
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: Math.max(0, (parent.width - parent.columnSpacing) / 2)
                                        spacing: 6
                                        CaptionText { text: "Idioma"; color: Theme.ink }
                                        VxComboBox { id: meetingLanguage; Layout.fillWidth: true; model: ["Português (Brasil)", "Detectar automaticamente", "Inglês", "Espanhol"] }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: Math.max(0, (parent.width - parent.columnSpacing) / 2)
                                        spacing: 6
                                        CaptionText { text: "Qualidade"; color: Theme.ink }
                                        VxComboBox { id: meetingQuality; Layout.fillWidth: true; model: ["Leve", "Equilibrada", "Alta precisão", "Rápida"]; Component.onCompleted: currentIndex = Math.max(0, model.indexOf(backend.recommendedProfile)) }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.columnSpan: parent.width < 760 ? 1 : 2
                                        spacing: 6
                                        CaptionText { text: "Áudio da reunião"; color: Theme.ink }
                                        VxComboBox {
                                            id: systemDevice
                                            Layout.fillWidth: true
                                            model: backend.meetingSystemDevices.map(function (device) { return device.name + (device.default ? " (padrão)" : ""); })
                                        }
                                    }
                                }

                                VxCheckBox { id: includeMicrophone; text: "Incluir meu microfone em trilha separada"; Layout.fillWidth: true }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    visible: includeMicrophone.checked
                                    spacing: 6
                                    CaptionText { text: "Microfone"; color: Theme.ink }
                                    VxComboBox { id: microphoneDevice; Layout.fillWidth: true; model: backend.meetingMicrophoneDevices.map(function (device) { return device.name; }) }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: signalRow.implicitHeight + 24
                                    radius: Theme.radiusSmall
                                    color: backend.meetingTested ? "#F0FAF4" : "#F7F8FA"
                                    border.width: 1
                                    border.color: backend.meetingTested ? "#B8E4C8" : Theme.line
                                    RowLayout {
                                        id: signalRow
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 12
                                        VxButton { text: "Testar sinal"; onClicked: backend.test_meeting_signal(systemDevice.currentIndex, includeMicrophone.checked, microphoneDevice.currentIndex) }
                                        CaptionText { Layout.fillWidth: true; text: backend.meetingTestMessage || "Teste as fontes antes de iniciar a captura."; color: backend.meetingTested ? Theme.success : Theme.muted; wrapMode: Text.Wrap }
                                    }
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    Item { Layout.fillWidth: true }
                                    VxButton {
                                        text: "Iniciar captura"
                                        primary: true
                                        enabled: captureConsent.checked && backend.meetingTested && backend.meetingSystemDevices.length > 0
                                        onClicked: backend.start_meeting_capture(captureConsent.checked, systemDevice.currentIndex, includeMicrophone.checked, microphoneDevice.currentIndex, ["pt", "auto", "en", "es"][meetingLanguage.currentIndex], ["Leve", "Equilibrada", "Alta precisão", "Rápida"][meetingQuality.currentIndex], "")
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: meetingProgress.implicitHeight + 52
                            radius: Theme.radiusLarge
                            color: Theme.surface
                            border.width: 1
                            border.color: Theme.line
                            visible: backend.meetingState === "capturing" || backend.meetingState === "stopping" || backend.meetingState === "transcribing"

                            ColumnLayout {
                                id: meetingProgress
                                anchors.fill: parent
                                anchors.margins: 26
                                spacing: 16
                                SectionTitle { text: backend.meetingState === "capturing" ? "Captura em andamento" : "Transcrição final em andamento" }
                                BodyText { text: backend.meetingMessage; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                RowLayout {
                                    Layout.fillWidth: true
                                    CaptionText { text: "Duração: " + backend.meetingDuration }
                                    Item { Layout.fillWidth: true }
                                    CaptionText { text: "Salvo até: " + backend.meetingLastSaved; color: Theme.success }
                                }
                                VxProgressBar {
                                    Layout.fillWidth: true
                                    from: 0
                                    to: 100
                                    value: backend.meetingState === "transcribing" ? backend.meetingProgress : 100
                                    indeterminate: backend.meetingState === "capturing" || backend.meetingState === "stopping"
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    CaptionText { text: "Saída" }
                                    VxProgressBar { Layout.preferredWidth: 140; from: 0; to: 1; value: backend.meetingSystemLevel }
                                    CaptionText { text: "Microfone"; visible: backend.meetingMicrophoneLevel > 0 }
                                    VxProgressBar { Layout.preferredWidth: 140; from: 0; to: 1; value: backend.meetingMicrophoneLevel; visible: backend.meetingMicrophoneLevel > 0 }
                                    Item { Layout.fillWidth: true }
                                    VxButton { text: "Encerrar e transcrever"; primary: true; visible: backend.meetingState === "capturing"; onClicked: backend.stop_meeting_capture() }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 156
                            radius: Theme.radiusLarge
                            color: Theme.surface
                            border.width: 1
                            border.color: Theme.line
                            visible: backend.meetingState === "completed"
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 24
                                Rectangle {
                                    Layout.preferredWidth: 42
                                    Layout.preferredHeight: 42
                                    radius: 21
                                    color: "#F0FAF4"
                                    Text { anchors.centerIn: parent; text: "\u2713"; color: Theme.success; font.family: "Manrope"; font.pixelSize: 20; font.weight: Font.Bold }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    SectionTitle { text: "Transcrição final pronta" }
                                    BodyText { text: backend.meetingMessage; color: Theme.muted; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                }
                                VxButton { text: "Revisar reunião"; primary: true; onClicked: backend.open_meeting_review(backend.meetingSessionId) }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            SectionTitle { text: "Reuniões salvas" }
                            Item { Layout.fillWidth: true }
                            CaptionText { text: backend.meetingSessions.length + " item(ns)" }
                        }
                        Repeater {
                            model: backend.meetingSessions
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 92
                                radius: Theme.radius
                                color: Theme.surface
                                border.width: 1
                                border.color: Theme.line
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    spacing: 14
                                    Rectangle {
                                        Layout.preferredWidth: 40
                                        Layout.preferredHeight: 40
                                        radius: 20
                                        color: Theme.primarySoft
                                        Text { anchors.centerIn: parent; text: "\u266B"; color: Theme.primaryDark; font.family: "Manrope"; font.pixelSize: 20; font.weight: Font.DemiBold }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        BodyText { text: modelData.title; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                                        CaptionText { text: modelData.status + "  •  " + modelData.duration }
                                    }
                                    VxButton {
                                        text: modelData.canReview ? "Reprocessar" : "Transcrever"
                                        visible: modelData.canTranscribe
                                        primary: !modelData.canReview
                                        onClicked: backend.resume_meeting_transcription(modelData.id)
                                    }
                                    VxButton {
                                        text: "Revisar"
                                        enabled: modelData.canReview
                                        onClicked: backend.open_meeting_review(modelData.id)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Revisão de reunião
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: root.pagePadding
                    spacing: 18
                    RowLayout {
                        Layout.fillWidth: true
                        PageTitle { text: backend.meetingReviewTitle; Layout.fillWidth: true; elide: Text.ElideMiddle }
                        VxButton { text: "Voltar"; onClicked: backend.navigate(7) }
                        VxButton { text: "Exportar"; primary: true; onClicked: root.openMeetingExport(backend.meetingReviewSessionId, backend.meetingReviewRunId) }
                    }
                    CaptionText { text: "Edite os trechos necessários. O texto reconhecido original permanece preservado."; Layout.fillWidth: true }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 10
                        model: backend.meetingReviewSegments
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: Math.max(94, meetingEdit.implicitHeight + 34)
                            radius: Theme.radius
                            color: Theme.surface
                            border.width: 1
                            border.color: modelData.attention ? "#F2C66D" : Theme.line
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 14
                                ColumnLayout {
                                    Layout.preferredWidth: 145
                                    CaptionText { text: modelData.time; color: Theme.muted }
                                    CaptionText { text: modelData.track; color: Theme.primaryDark }
                                }
                                VxTextArea {
                                    id: meetingEdit
                                    text: modelData.text
                                    Layout.fillWidth: true
                                    Layout.minimumHeight: 70
                                    onEditingFinished: backend.revise_meeting_segment(modelData.id, text)
                                }
                                CaptionText { text: modelData.attention ? "Verifique" : "Normal"; color: modelData.attention ? "#9A6500" : Theme.success; Layout.preferredWidth: 82 }
                            }
                        }
                    }
                }
            }
        }
    }
}
