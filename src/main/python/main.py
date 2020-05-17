import os
import sys
import traceback

from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext,
)
from PyQt5 import QtGui, QtCore, QtWidgets

# Custom
from ui import mainwindow, config
from ftp.ftp_client import FTPClient, FTPFile
from ftp.util import get_cfg


class ftpThread(QtCore.QThread):
    download_complete_signal = QtCore.pyqtSignal(FTPFile)

    def __init__(self, ftp_client: FTPClient):
        super().__init__()
        self.ftp_client = ftp_client

    def __del__(self):
        self.wait()

    def run(self):
        try:
            self.ftp_client.download(self.download_complete_signal)
        except Exception as e:
            print(traceback.format_exc())


class MainWindow(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.ftp_cfg = get_cfg('config.yml')
        self.setupUi(self)

        # action
        self.actionConfig.triggered.connect(self.config)

        # button
        self.pushButtonApply.clicked.connect(self.apply)
        self.pushButtonDownload.clicked.connect(self.download)
        self.pushButtonDownload.setEnabled(False)
        self.pushButtonCancel.clicked.connect(self.cancel)

        # set config
        self.lineEditHost.setText(self.ftp_cfg['url'])
        self.lineEditUser.setText(self.ftp_cfg['username'])
        self.lineEditPassword.setText(self.ftp_cfg['password'])

        # list view setting
        self.to_download_model = QtGui.QStandardItemModel()
        self.downloaded_model = QtGui.QStandardItemModel()
        self.listViewFileToDownload.setModel(self.to_download_model)
        self.listViewDownloadComplete.setModel(self.downloaded_model)

    def config(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '.', '(*.yml)')[0]

        # TODO : 파일 내용 적용하기
        configDialog = ConfigDialog(self, filename)
        configDialog.exec_()

    def apply(self):
        """다운로드 할 목록 리스트 뷰에 추가"""
        # initialize list view widget
        self.to_download_model.clear()
        self.downloaded_model.clear()

        url = self.lineEditHost.text()
        username = self.lineEditUser.text()
        password = self.lineEditPassword.text()

        # ftp client setting
        self.ftp_client = ftp_client = FTPClient(url, username, password)
        if self.ftp_cfg["passive_mode"]:
            ftp_client.set_passive_mode()
        else:
            ftp_client.set_active_mode()
        ftp_client.pattern = self.ftp_cfg["pattern"]

        for remote_dir, local_dir in zip(self.ftp_cfg['remote_dirs'], self.ftp_cfg['local_dirs']):
            self.ftp_client.apply_file_to_download(remote_dir, local_dir)

        for ftp_file in self.ftp_client.file_to_download:
            item = QtGui.QStandardItem(ftp_file.ftp_path)
            self.to_download_model.appendRow(item)

        self.progressBar.setMaximum(len(self.ftp_client.file_to_download))
        self.progressBar.setValue(0)

        self.pushButtonApply.setEnabled(False)
        self.pushButtonDownload.setEnabled(True)

        QtWidgets.QMessageBox.information(self, 'Done!', '파일 목록을 모두 가져왔습니다!')

    def download(self):
        self.ftp_thread = ftpThread(self.ftp_client)
        
        self.ftp_thread.download_complete_signal.connect(self.append_downloaded_file)
        self.ftp_thread.finished.connect(self.done)
        self.ftp_thread.start()

        self.pushButtonDownload.setEnabled(False)
        self.pushButtonApply.setEnabled(True)

    def cancel(self):
        pass

    def append_downloaded_file(self, ftp_file: FTPFile):
        item = QtGui.QStandardItem(ftp_file.local_path)
        self.downloaded_model.appendRow(item)
        self.progressBar.setValue(self.progressBar.value() + 1)

    def done(self):
        self.pushButtonDownload.setEnabled(True)
        QtWidgets.QMessageBox.information(self, 'Done!', 'Done download')
        

    def ftp_download(self):
        self.ftp_thread = ftpThread()
        
        self.ftp_thread.append_text_signal.connect(self.append_text)
        self.ftp_thread.finished.connect(self.done)
        self.ftp_thread.start()

        self.download_btn.setEnabled(False)


class ConfigDialog(QtWidgets.QDialog, config.Ui_Dialog):

    def __init__(self, parent=None, filename=None):
        super(ConfigDialog, self).__init__(parent)
        self.setupUi(self)

        if not filename:
            return

        ftp_cfg = get_cfg(filename)
        self.lineEditHost.setText(ftp_cfg['url'])
        self.lineEditUsername.setText(ftp_cfg['username'])
        self.lineEditPassword.setText(ftp_cfg['password'])
        if ftp_cfg['passive_mode'] == False:
            self.radioButtonActive.setChecked(True)
        else:
            self.radioButtonDefault.setChecked(True)
        self.textEditRemoteDirs.setText('\n'.join(ftp_cfg['remote_dirs']))
        self.textEditLocalDirs.setText('\n'.join(ftp_cfg['local_dirs']))
        self.lineEditFilePattern.setText(ftp_cfg['pattern'])


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
