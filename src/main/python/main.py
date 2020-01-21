from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext,
    cached_property
)
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QStatusBar,
    QAction,
    QTextEdit,
    QLineEdit,
    QLabel,
)
from PyQt5.QtGui import (
    QImage,
    QIcon,
)
from PyQt5.QtCore import (
    QSize,
)

import os
import sys
import traceback

# Custom
from ftp import ftp_downloader
from ftp.util import get_cfg

class AppContext(ApplicationContext):
    def __init__(self, *args, **kwargs):
        super(AppContext, self).__init__(*args, **kwargs)

    @cached_property
    def main_window(self):
        return MainWindow(self)

    @cached_property
    def site_manager(self):
        return QIcon(self.get_resource('images/folder.png'))

    def run(self):
        self.main_window.show()
        return self.app.exec_()


class MainWindow(QMainWindow):
    def __init__(self, ctx):
        super(MainWindow, self).__init__()

        self.ctx = ctx
        self.ftp_cfg = get_cfg('config.yml')
        self.is_download = False
        self.setWindowTitle('filedown')

        self.resize(600, 400)

        # set toolbar
        self.toolbar = self.addToolBar('Config')

        # set statusbar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # set widget
        win = QWidget()
        vb = QVBoxLayout()

        # toolbar - action
        site_manager_action = QAction(self.ctx.site_manager, 'Site Manager', self)
        site_manager_action.triggered.connect(self.open_site_manager)
        self.toolbar.addAction(site_manager_action)

        # config information
        hb = QHBoxLayout()
        hb.addWidget(QLabel("url:"))
        self.url_edit = QLineEdit()
        hb.addWidget(self.url_edit)
        hb.addWidget(QLabel("user:"))
        self.user_edit = QLineEdit()
        hb.addWidget(self.user_edit)
        hb.addWidget(QLabel("pw:"))
        self.pw_edit = QLineEdit()
        hb.addWidget(self.pw_edit)
        vb.addLayout(hb)

        # text board
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)

        font = text_edit.font()
        font.setFamily('Courier')
        font.setPointSize(10)
        
        vb.addWidget(text_edit)
        self.text_edit = text_edit

        # download button
        download_btn = QPushButton('download', self)
        download_btn.clicked.connect(self.ftp_download)

        vb.addWidget(download_btn, alignment=QtCore.Qt.AlignRight)

        win.setLayout(vb)
        self.setCentralWidget(win)

        # set config
        self.url_edit.setText(self.ftp_cfg['url'])
        self.user_edit.setText(self.ftp_cfg['username'])
        self.pw_edit.setText(self.ftp_cfg['password'])

        self.show()

    def open_site_manager(self):
        print('click')

    def ftp_download(self):
        if self.is_download:
            print('is downloading')
            return
        self.is_download = True
        self.text_edit.append('downloading...')
        print(self.text_edit.toPlainText())
        try:
            ftp_downloader.download(self.ftp_cfg, self.text_edit.append)
        except Exception as e:
            print(traceback.format_exc())
        finally:
            self.is_download = False
        self.text_edit.append('download complete')


if __name__ == '__main__':
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)