import QtQuick 2.6
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3
import org.kde.kirigami 2.8 as Kirigami

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
                width: parent.width
                height: profiles.height
                anchors.centerIn: parent
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
                            text: name
                            onClicked: window.openProfile(profileid)
                            visible: true
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

                Rectangle {
                    color: "#00000000"
                    height: 8
                }
                Label {
                    id: editProfileNameTip
                    objectName: "editProfileNameTip"
                    text: "Choose a name for your profile:"
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.2
                }
                TextField {
                    id: editProfileName
                    objectName: "editProfileName"
                }
                Label {
                    id: editProfileNameEmpty
                    objectName: "editProfileNameEmpty"
                    text: "Please specify a name for this profile"
                    color: Kirigami.Theme.negativeTextColor
                    visible: false
                }

                Rectangle {
                    color: "#00000000"
                    height: 8
                }
                Label {
                    id: editProfileOptionsTip
                    objectName: "editProfileOptionsTip"
                    text: "Profile options:"
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.2
                }
                CheckBox {
                    id: forceDarkMode
                    objectName: "forceDarkMode"
                    text: "Force dark mode on websites (may break some websites)"
                }
                // CheckBox {
                //     id: incognitoMode
                //     objectName: "incognitoMode"
                //     text: "Always start in Incognito Mode"
                // }
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
