import QtQuick 2.6
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3
import org.kde.kirigami 2.13 as Kirigami

ApplicationWindow {
    id: window
    objectName: "mainwnd"
    visible: true
    width: 1020
    height: 600
    title: "APPTITLE" // Changed by feren-storium-ice

    //SIGNALS
    signal createProfile()
    signal openProfile(var profileid)


    Kirigami.Theme.inherit: true
    color: Kirigami.Theme.backgroundColor

    property var buttonRowMargin: 5

    SwipeView {
        id: pages
        objectName: "pages"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: buttonRow.top
        anchors.bottomMargin: buttonRowMargin
        Kirigami.Theme.colorSet: Kirigami.Theme.View

        background: Rectangle {
            color: Kirigami.Theme.backgroundColor
        }

        Item {
            id: profileSelect

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: profilesHeader
                    objectName: "profilesHeader"
                    text: "Who's using APPTITLE?" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: profilesSubheader
                    objectName: "profilesSubheader"
                    text: "Select your profile from the options below to begin.\nIf you are a guest, hit "+'"'+"Browse as Guest"+'"'+" below, otherwise if you're a new user hit "+'"'+"Add a profile"+'"'+" instead to begin."
                }
            }

            ScrollView {
                width: parent.width > profiles.width ? profiles.width : parent.width // center the profiles list
                height: profiles.height + Kirigami.Units.gridUnit
                anchors.centerIn: parent
                anchors.verticalCenterOffset: Kirigami.Units.gridUnit * 0.5 // rebalance the centering
                clip: true
                contentWidth: profiles.width
                RowLayout {
                    id: profiles
                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }


                    Repeater {
                        objectName: "profilesRepeater"
                        model: ProfilesModel
                        delegate: Button {
                            id: buttondeleg1
                            Layout.preferredWidth: 7.5 * Kirigami.Units.gridUnit
                            Layout.preferredHeight: 7 * Kirigami.Units.gridUnit
                            onClicked: window.openProfile(profileid)

                            contentItem: ColumnLayout {
                                Kirigami.Avatar {
                                    name: myname
                                    initialsMode: Kirigami.Avatar.InitialsMode.UseIcon
                                    readonly property int size: 3 * Kirigami.Units.gridUnit
                                    width: size
                                    height: size
                                    anchors.centerIn: parent //FIXME: it misaligns without this
                                }
                                Text {
                                    text: myname
                                    font: buttondeleg1.font
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }


                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }
                }
            }
        }

        Item {
            id: browserSelect

            ColumnLayout {
                id: browserSelectCaption
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: browsersHeader
                    objectName: "browsersHeader"
                    text: "Choose a browser to launch APPTITLE" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: browsersSubheader
                    objectName: "browsersSubheader"
                    text: "The browser used to launch this application is missing or has been removed.\nTo continue, please choose a replacement browser below."
                }
            }

            ScrollView {
                width: browsers.width
                anchors.top: browserSelectCaption.bottom //need to do this differently so it doesn't overlap or underlap the caption
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                clip: true
                contentHeight: browsers.height
                ColumnLayout {
                    id: browsers

                }
            }
        }

        Item {
            id: profileManager

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: manageHeader
                    objectName: "manageHeader"
                    text: "Manage APPTITLE Profiles" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: manageSubheader
                    objectName: "manageSubheader"
                    text: "Select a profile from the options below, and then choose what you want to do with the profile below.\nOnce you are done managing profiles, hit Done below."
                }
            }

            ScrollView {
                width: parent.width
                height: profiles2.height
                anchors.centerIn: parent
                clip: true
                contentWidth: profiles2.width
                RowLayout {
                    id: profiles2
                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }


                    Button {
                        text: "dummy button"
                    }
                    Button {
                        text: "dummy button"
                    }


                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }
                }
            }
        }

        Item {
            id: profileEditor

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: createHeader
                    objectName: "createHeader"
                    text: "Create a profile" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: createSubheader
                    objectName: "createSubheader"
                    text: "Choose your name, and options for your profile.\nOnce you are done. hit Finish below."
                }
            }
        }

        Item {
            id: profileEditing

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: editHeader
                    objectName: "editHeader"
                    text: "Configuring Profile" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: editSubheader
                    objectName: "editSubheader"
                    text: "Choose your name, and options for your profile.\nOnce you are done. hit Finish below."
                }
            }

            TextField {
                id: editProfileName
                objectName: "editProfileName"
                horizontalAlignment: Text.AlignRight
                anchors {
                    right: editingAvatar.left
                    verticalCenter: parent.verticalCenter
                    rightMargin: Kirigami.Units.largeSpacing * 2
                }

                Text {
                    text: "Profile name"
                    opacity: 0.5
                    visible: !editProfileName.text
                    anchors {
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                        rightMargin: Kirigami.Units.smallSpacing
                    }
                }
            }
            Label {
                id: editProfileNameEmpty
                objectName: "editProfileNameEmpty"
                text: "Please specify a name for this profile"
                color: Kirigami.Theme.negativeTextColor
                visible: false
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignRight

                anchors {
                    top: editProfileName.bottom
                    topMargin: Kirigami.Units.smallSpacing
                    left: parent.left
                    right: editProfileName.right
                }
            }

            Kirigami.Avatar {
                id: editingAvatar
                name: editProfileName.text
                initialsMode: Kirigami.Avatar.InitialsMode.UseIcon
                readonly property int size: 8 * Kirigami.Units.gridUnit
                width: size
                height: size
                anchors.centerIn: parent
            }

            CheckBox {
                id: forceDarkMode
                objectName: "forceDarkMode"
                text: "Force dark mode"
                anchors {
                    left: editingAvatar.right
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    leftMargin: Kirigami.Units.largeSpacing * 2
                }
            }
            Label {
                id: forceDarkModeHint
                objectName: "forceDarkModeHint"
                text: "May break some websites"
                wrapMode: Text.WordWrap
                elide: Text.ElideRight

                anchors {
                    top: forceDarkMode.bottom
                    left: forceDarkMode.left
                    right: parent.right
                }
            }

            // TODO: Page for profile editing/creation

        }
    }

    RowLayout {
        id: buttonRow
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: buttonRowMargin

        // Profile Select Buttons
        Button {
            text: "Browse as Guest (dummy)"
            visible: pages.currentIndex == 0 ? true : false
        }
        // Profile Management Buttons
        Button {
            text: "Edit profile... (dummy)"
            icon {
                name: "document-edit"
            }
            visible: pages.currentIndex == 2 ? true : false
        }
        Button {
            text: "Delete profile (dummy)"
            icon {
                name: "delete"
                color: Kirigami.Theme.negativeTextColor
            }
            visible: pages.currentIndex == 2 ? true : false
        }
        // Profile Creation Buttons
        Button {
            text: "Cancel (dummy)"
            icon {
                name: "dialog-cancel"
            }
            visible: pages.currentIndex == 3 ? true : false
        }
        // Profile Editor Buttons
        Button {
            text: "Manage bonuses in Store... (dummy)"
            icon {
                name: "feren-store"
            }
            visible: pages.currentIndex == 4 ? true : false
        }

        // Separator
        Rectangle {
            id: rectangle
            color: "#00000000"
            Layout.fillWidth: true
        }
        // Profile Select Buttons
        Button {
            text: "Manage profiles... (dummy)"
            icon {
                color: Kirigami.Theme.neutralTextColor
            }
            visible: pages.currentIndex == 0 ? true : false
        }
        Button {
            text: "Add a profile... (dummy)"
            icon {
                name: "list-add"
            }
            visible: pages.currentIndex == 0 ? true : false
        }
        // Browser Select Buttons
        Button {
            text: "Confirm (dummy)"
            icon {
                name: "dialog-apply"
            }
            visible: pages.currentIndex == 1 ? true : false
        }
        // Profile Management Buttons
        Button {
            text: "Done (dummy)"
            icon {
                color: Kirigami.Theme.positiveTextColor
            }
            visible: pages.currentIndex == 2 ? true : false
        }
        // Profile Creation Buttons
        Button {
            text: "Finish (dummy)"
            icon {
                name: "dialog-apply"
            }
            visible: pages.currentIndex == 3 ? true : false
        }
        // Profile Editor Buttons
        Button {
            text: "Done"
            icon {
                color: Kirigami.Theme.positiveTextColor
            }
            visible: pages.currentIndex == 4 ? true : false
            onClicked: window.createProfile()
        }

    }
}
