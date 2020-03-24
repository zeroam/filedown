import threading
from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext,
    cached_property
)
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QMainWindow,
    QDialog,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QStatusBar,
    QAction,
    QTextEdit,
    QPlainTextEdit,
    QLineEdit,
    QLabel,
    QMessageBox,
)
from PyQt5.QtGui import (
    QImage,
    QIcon,
)
from PyQt5.QtCore import (
    QSize,
    QCoreApplication,
    QThread,
    pyqtSignal,
)

import os
import sys
import traceback

# Custom
from ui import mainwindow, config
from ftp.ftp_client import FTPClient
from ftp.util import get_cfg


class ftpThread(QThread):
    append_text_signal = pyqtSignal(str)

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


class MainWindow(QMainWindow, mainwindow.Ui_MainWindow):

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
        # TODO : 파일 읽기 (.yml)

        # TODO : 파일 내용 적용하기
        configDialog = ConfigDialog(self)
        configDialog.exec_()

    def apply(self):
        url = self.lineEditHost.text()
        username = self.lineEditUser.text()
        password = self.lineEditPassword.text()
        self.ftp_client = FTPClient(url, username, password)
        # self.ftp_client.apply_file_to_download(self.ftp_cfg['ftp_dir'])
        for remote_dir, local_dir in zip(self.ftp_cfg['remote_dirs'], self.ftp_cfg['local_dirs']):
            self.ftp_client.apply_file_to_download(remote_dir, local_dir)

        model = QtGui.QStandardItemModel()
        self.listViewFileToDownload.setModel(model)
        for ftp_file in self.ftp_client.file_to_download:
            item = QtGui.QStandardItem(ftp_file.ftp_path)
            model.appendRow(item)

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


class ConfigDialog(QDialog, config.Ui_Dialog):

    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent)
        self.setupUi(self)


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)