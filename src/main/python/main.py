import os
import sys
import traceback

from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext,
)
from PyQt5 import QtGui, QtCore, QtWidgets

# Custom
from ui import mainwindow, config
from ftp.ftp_client import FTPClient
from ftp.util import get_cfg


class ftpThread(QtCore.QThread):
    append_text_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ftp_cfg = get_cfg('config.yml')

    def __del__(self):
        self.wait()

    def run(self):
        self.append_text_signal.emit('start downloading...')
        try:
            ftp_downloader.download(self.ftp_cfg)
        except Exception as e:
            print(traceback.format_exc())
        self.append_text_signal.emit('complete downloading...')


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
        self.pushButtonCancel.clicked.connect(self.cancel)

        # set config
        self.lineEditHost.setText(self.ftp_cfg['url'])
        self.lineEditUser.setText(self.ftp_cfg['username'])
        self.lineEditPassword.setText(self.ftp_cfg['password'])

    def config(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '.', '(*.yml)')[0]

        # TODO : 파일 내용 적용하기
        configDialog = ConfigDialog(self, filename)
        configDialog.exec_()

    def apply(self):
        """다운로드 할 목록 리스트 뷰에 추가"""
        url = self.lineEditHost.text()
        username = self.lineEditUser.text()
        password = self.lineEditPassword.text()
        self.ftp_client = FTPClient(url, username, password)

        for remote_dir, local_dir in zip(self.ftp_cfg['remote_dirs'], self.ftp_cfg['local_dirs']):
            self.ftp_client.apply_file_to_download(remote_dir, local_dir)

        model = QtGui.QStandardItemModel()
        self.listViewFileToDownload.setModel(model)
        for ftp_file in self.ftp_client.file_to_download:
            item = QtGui.QStandardItem(ftp_file.ftp_path)
            model.appendRow(item)

        self.progressBar.setMaximum(len(self.ftp_client.file_to_download))
        self.progressBar.setValue(0)

        QMessageBox.information(self, 'Done!', '파일 목록을 모두 가져왔습니다!')
        self.pushButtonApply.setEnabled(False)

    def download(self):
        pass

    def cancel(self):
        pass

    def append_text(self, text):
        self.text_edit.appendPlainText(text)

    def done(self):
        self.download_btn.setEnabled(True)
        QMessageBox.information(self, 'Done!', 'Done download')
        

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


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
