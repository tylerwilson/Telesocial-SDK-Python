#
# PyQt/PySide GUI for testing TeleSocial Python API
#

import sys

UI_FILE = "telesocial-gui.ui"

try:
    # PySide version
    raise
    from PySide import QtCore, QtGui
    from PySide.QtUiTools import QUiLoader
except:
    # PyQt version
    from PyQt4 import QtCore, QtGui, uic
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot


sys.path.append("..")
import telesocial

#API_KEY = "f180804f-5eda-4e6b-8f4e-ecea52362396" # commonly seen in many of the examples
API_KEY = "65a1f558-1975-4cf3-9590-690e076633ba" # Python SDK-specific test key


class MyMainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        
        # the GUI is loaded here
        self.ui = None
        
        if 'QUiLoader' in globals():
            # PySide
            self.ui = loadUi(UI_FILE, self)
        if 'uic' in globals():
            # PyQt
            ui_class, widget_class = uic.loadUiType(UI_FILE) 
            self.ui = ui_class() 
            self.ui.setupUi(self)

        self.show()
        
        # telesocial client
        self.client = telesocial.SimpleClient(API_KEY)
    
    def get_api_key(self):
        return self.ui.editAPIKey.currentText()
            
    def showMessage(self, msg):
        self.statusBar().showMessage(msg)
        
    # Menu items
    
    @QtCore.Slot()
    def on_actionExit_triggered(self):
        print("on_actionExit_triggered")
        self.close()
        
    @QtCore.Slot()
    def on_actionAbout_triggered(self):
        print("on_actionAbout_triggered")
        QtGui.QMessageBox.about(self, "About Me", "Simple application to test TeleSocial API")
        
    @QtCore.Slot()
    def on_buttonVersion_released(self):
        print("getting version information")
        try:
            version = self.client.version()
            QtGui.QMessageBox.about(self, "Version", "TeleSocial API version is {}.{}.{}".format(*version))
        except telesocial.TelesocialServiceError as e:
            print(e)

    # Registration Tab
    
    @QtCore.Slot()
    def on_buttonNetworkAdd_released(self):
        """Add a new network id registration"""
        print("adding registration")
        try:
            id = self.ui.editNetworkID.text()
            phone = self.ui.editPhone.text()
            print("id:{}, phone:{}".format(id, phone))
            res = self.client.network_id_register(str(id), str(phone))
            print(res.code, res.data)
            self.showMessage(str(res.data))
        except telesocial.TelesocialError as e:
            self.showMessage(str(e))
            print(e)
            
    @QtCore.Slot()
    def on_buttonNetworkAdd2_released(self):
        """Add a new network id registration via popup dialog"""
        dlg = RegisterDialog(self)
#        dlg.show()
        response = dlg.exec_()
        print(response)
        id = dlg.ui.editID.text()
        phone = dlg.ui.editPhone.text()
        if id and phone:
            try:
                print("id:{}, phone:{}".format(id, phone))
                res = self.client.network_id_register(str(id), str(phone))
                print(res.code, res.data)
                self.showMessage(str(res.data))
            except telesocial.TelesocialError as e:
                print(e)
            
    @QtCore.Slot()
    def on_buttonNetworkRefresh_released(self):
        """Update the list of Network IDs in the List Widget"""
        print("getting Network IDs")
        try:
            res = self.client.network_id_list()
            print("ids:", res.code, res.data)
            self.showMessage(str(res.data))
            print(res.data.keys())
            self.ui.listNetworkIDs.clear()
            for id in res.data['NetworkidListResponse']['networkids']:
                self.ui.listNetworkIDs.addItem(str(id))
                self.ui.listNetworkIDs2.addItem(str(id)) # for the list in the conference tab
        except telesocial.TelesocialError as e:
            print(e)

    @QtCore.Slot()
    def on_buttonNetworkStatus_released(self):
        # retrieve status and display
        #items = self.ui.listNetworkIDs.selectedItems()
        id = self.ui.editNetworkID.text()
        #for item in items:
        print("status for network id ", id)
        res = self.client.network_id_status(str(id))
        print(res.code, res.data)
        self.showMessage(str(res.data))

    @QtCore.Slot()
    def on_buttonNetworkStatus1_released(self):
        # status of selected item
        items = self.ui.listNetworkIDs.selectedItems()
        for item in items:
            id = str(item.text())
            print("status for network id ", id)
            res = self.client.network_id_status(str(id))
            print(res.code, res.data)
            self.showMessage(str(res.data))

    @QtCore.Slot()
    def on_buttonNetworkDelete_released(self):
        # delete all selected items
        items = self.ui.listNetworkIDs.selectedItems()
        for item in items:
            id = str(item.text())
            print("deleting network id ", id)
            res = self.client.network_id_delete(id)
            print(res.code, res.data)
            self.showMessage(str(res.data))

    # Conference Tab
    
    @QtCore.Slot()
    def on_buttonConferenceCreate_released(self):
        print("creating conference")
        try:
            network_ids = self.ui.listNetworkIDs2.selectedItems()
            if network_ids:
                # only use the first one
                network_id = network_ids[0].text() 
                res = self.client.conference_create(str(network_id))
                self.showMessage(str(res.data))
        except telesocial.TelesocialError as e:
            print(e)
        
    @QtCore.Slot()
    def on_buttonConferenceAdd_released(self):
        print("adding to conference")
        items = self.ui.listConferenceIDs.selectedItems()
        if items:
            conference_id = str(items[0].text(0))
            try:
                items2 = self.ui.listNetworkIDs2.selectedItems()
                for item2 in items2:
                    network_id = str(item2.text())
                    self.client.conference_add(conference_id, str(network_id.text()))
            except telesocial.TelesocialError as e:
                print(e)

    def on_buttonConferenceClose_released(self):
        print("closing conference")
        items = self.ui.listConferenceIDs.selectedItems()
        for item in items:
            conference_id = str(item.text(0))
            try:
                res = self.client.conference_close(conference_id)
                print(res.code, res.data)
                self.showMessage(str(res.data))
            except telesocial.TelesocialError as e:
                print(e)
                self.showMessage(str(e))

    @QtCore.Slot()
    def on_buttonConferenceDetails_released(self):
        print("getting conference details")
        items = self.ui.listConferenceIDs.selectedItems()
        for item in items:
            try:
                conference_id = item.text(0)
                res = self.client.conference_details(str(conference_id))
                print(res.code, res.data)
                self.showMessage(str(res.data))
            except telesocial.TelesocialError as e:
                print(e)

    @QtCore.Slot()
    def on_buttonConferenceRefresh_released(self):
        """Update the list of Conference in the List Widget"""
        print("getting conferences")
        try:
            res = self.client.conference_list()
            print(res.code, res.data)
            self.ui.listConferenceIDs.clear()
            for id in res.data['ConferenceListResponse']['active']:
                QtGui.QTreeWidgetItem(self.ui.listConferenceIDs, [str(id), 'active'])
                #self.ui.listConferenceIDs.addItem(str(id))
            for id in res.data['ConferenceListResponse']['inactive']:
                QtGui.QTreeWidgetItem(self.ui.listConferenceIDs, [str(id), 'inactive'])
                #self.ui.listConferenceIDs.addItem(str(id))
        except telesocial.TelesocialError as e:
            print(e)

    # Media Tab

    @QtCore.Slot()
    def on_buttonMediaCreate_released(self):
        print("creating new media resource")
        try:
            res = self.client.media_create()
            print(res.code, res.data)
            self.showMessage(str(res.data))
            id = res.data['MediaResponse']['mediaId']
            self.ui.editMediaID.setText(id)
        except telesocial.TelesocialError as e:
            print(e)
        
    @QtCore.Slot()
    def on_buttonMediaRecord_released(self):
        print("recording into a media resource")
        items = self.ui.listNetworkIDs.selectedItems()
        if items:
            # just use the first one
            network_id = str(items[0].text())
            media_id = str(self.ui.editMediaID.text())
            if network_id and media_id:
                try:
                    res = self.client.media_record(media_id, network_id)
                    print(res.code, res.data)
                    self.showMessage(str(res.data))
                except telesocial.TelesocialError as e:
                    print(e)
        
    @QtCore.Slot()
    def on_buttonMediaBlast_released(self):
        print("sending Blast to network IDs")
        media_id = None
        network_id = None
        
        # just use the first selected media ID
        items = self.ui.listMediaIDs.selectedItems()
        if items:
            media_id = str(items[0].text(0))

        items = self.ui.listNetworkIDs.selectedItems()
        for item in items:
            network_id = str(item.text())
            
            if network_id and media_id:
                try:
                    res = self.client.media_blast(media_id, network_id)
                    print(res.code, res.data)
                    self.showMessage(str(res.data))
                except telesocial.TelesocialError as e:
                    print(e)
        
    @QtCore.Slot()
    def on_buttonUploadGrant_released(self):
        print("requesting upload grant")
        media_id = str(self.ui.editMediaID.text())
        if not media_id:
            print("Need Media ID first")
            return
        try:
            res = self.client.media_request_upload_grant(media_id)
            print(res.code, res.data)
            self.showMessage(str(res.data))
            grant_id = res.data['UploadResponse']['grantId']
            self.ui.editUploadGrant.setText(grant_id)
        except telesocial.TelesocialError as e:
            print(e)
            
    @QtCore.Slot()
    def on_buttonMediaRefresh_released(self):
        """Update the list of Media IDs in the List Widget"""
        print("getting Media IDs")
        try:
            res = self.client.media_list()
            print(res.code, res.data)
            self.showMessage(str(res.data))
            self.ui.listMediaIDs.clear()
            for id in res.data['MediaidListResponse']['uploaded']:
                #self.ui.listMediaIDs.addItem(str(id))
                QtGui.QTreeWidgetItem(self.ui.listMediaIDs, [id, 'uploaded'])
            for id in res.data['MediaidListResponse']['recorded']:
                #self.ui.listMediaIDs.addItem(str(id))
                QtGui.QTreeWidgetItem(self.ui.listMediaIDs, [id, 'recorded'])
        except telesocial.TelesocialError as e:
            print(e)

    @QtCore.Slot()
    def on_buttonMediaStatus_released(self):
        # get some stats about this media
        items = self.ui.listMediaIDs.selectedItems()
        for item in items:
            id = str(item.text(0))
            print("getting status for ", id)
            try:
                res = self.client.media_status(id)
                print(res.code, res.data)
                self.showMessage(str(res.data))
#                if 'MediaResponse' in res.data:
#                    info = res.data['MediaResponse']
#                    msg = "downloadUrl:{}\nfileSize:{}".format(info['downloadUrl'], info['fileSize'])
#                    QtGui.QMessageBox.information(self, "Media Status", msg)
            except telesocial.TelesocialError as e:
                print(e)

    @QtCore.Slot()
    def on_buttonMediaDelete_released(self):
        # delete all selected items
        items = self.ui.listMediaIDs.selectedItems()
        for item in items:
            id = str(item.text(0))
            print("deleting ", id)
            res = self.client.media_remove(id)
            print(res.code, res.data)
            self.showMessage(str(res.data))

    @QtCore.Slot()
    def on_buttonMediaChoose_released(self):
        # get an mp3 file from the FS
        fileName = QtGui.QFileDialog.getOpenFileName(self, caption="Open Media", filter="MP3 Files (*.mp3)")
        if fileName:
            self.ui.editMediaFile.setText(fileName)

    @QtCore.Slot()
    def on_buttonMediaDownload_released(self):
        # retrieve and save the given media to the local FS
        items = self.ui.listMediaIDs.selectedItems()
        for item in items:
            media_id = str(item.text())
            self.client.download_file(media_id, "temp.mp3")

    @QtCore.Slot()
    def on_buttonMediaUpload_released(self):
        # get an mp3 file from the FS
        print("sending mp3 file to server")
        #media_id = str(self.ui.editMediaID.text())
        grant_id = str(self.ui.editUploadGrant.text())
        file_name = str(self.ui.editMediaFile.text())
        if grant_id and file_name:
            res = self.client.upload_file(grant_id, file_name)
            print(res)
            self.showMessage(str(res))


class RegisterDialog(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(RegisterDialog, self).__init__(parent)
        
        # the GUI is loaded here
        self.ui = None
        
        if 'QUiLoader' in globals():
            # PySide
            self.ui = loadUi("register-dlg.ui", self)
        if 'uic' in globals():
            # PyQt
            ui_class, widget_class = uic.loadUiType("register-dlg.ui") 
            self.ui = ui_class() 
            self.ui.setupUi(self)

        self.show()
        
    def accept(self):
        super(RegisterDialog, self).accept()
        print("accept")
        return (self.ui.editID, self.ui.editPhone)
        
                
class MyApp(QtGui.QApplication):
    
    def __init__(self):
        super(MyApp, self).__init__(sys.argv)
        self.frame = MyMainWindow()
        
    def main(self):
        app.exec_()
        
        
if 'QUiLoader' in globals():
    class MyQUiLoader(QUiLoader):
        def __init__(self, baseinstance):
            super(MyQUiLoader, self).__init__()
            self.baseinstance = baseinstance
    
        def createWidget(self, className, parent=None, name=""):
            widget = super(MyQUiLoader, self).createWidget(className, parent, name)
            if parent is None:
                return self.baseinstance
            else:
                setattr(self.baseinstance, name, widget)
                return widget
    
    def loadUi(uifile, baseinstance=None):
        loader = MyQUiLoader(baseinstance)
        ui = loader.load(uifile)
        QtCore.QMetaObject.connectSlotsByName(ui)
        return ui


if __name__ == "__main__":
    app = MyApp()
    sys.exit(app.main())        