import QtQuick.Layouts 1.4
import QtQuick 2.4
import QtQuick.Controls 2.0
import org.kde.kirigami 2.4 as Kirigami

import Mycroft 1.0 as Mycroft

Mycroft.PaginatedDelegate {
    id: root
    graceTime: 60 * 1000
    property var upperText
    property var lowerText
    property var imgLink
    backgroundImage: imgLink
    switchHeight: height
    switchWidth: width
    backgroundDim: 0.8

    Kirigami.Page {
        ColumnLayout {
            id: grid
            Layout.fillWidth: true
            width: parent.width
            spacing: Kirigami.Units.largeSpacing

            Item {
                height: Kirigami.Units.largeSpacing * 4
            }

            Kirigami.Heading {
                id: title
                Layout.alignment: Qt.AlignHCenter
                level: 1
                Layout.columnSpan: 2
                wrapMode: Text.WordWrap
                font.capitalization: Font.AllUppercase
                text: upperText
            }
            Image {
                id: img
                fillMode: Image.PreserveAspectCrop
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Kirigami.Units.gridUnit * 10
                Layout.preferredHeight: Kirigami.Units.gridUnit * 10
                source: imgLink
            }
            Kirigami.Heading {
                id: answer
                Layout.alignment: Qt.AlignHCenter
                level: 2
                wrapMode: Text.WordWrap
                font.capitalization: Font.Capitalize
                text: lowerText
            }
        }
    }
}

