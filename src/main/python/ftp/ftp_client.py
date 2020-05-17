import os
import re
import shutil
import ftplib
import logging
import posixpath

from ftp.ftp_file import FTPFile


class FTPClient:

    def __init__(self, url: str, username: str='ananoymous', password: str='anonymous@'):
        self.url = url
        self.username = username
        self.password = password
        self.pattern = None

        self._passive_mode = True
        self._ftp_handler = None
        self._file_to_download = list()
        self._file_downloaded = list()

    @property
    def file_to_download(self) -> list:
        return self._file_to_download

    @property
    def file_downloaded(self) -> list:
        return self._file_downloaded

    def set_active_mode(self) -> None:
        self._passive_mode = False

    def set_passive_mode(self) -> None:
        self._passive_mode = True

    def download(self, signal=None) -> None:
        self._connect()

        # TODO: 다운로드 실패한 파일에 대한 처리 필요
        while self._file_to_download:
            ftp_file = self._file_to_download.pop(0)
            if self._download_file(ftp_file):
                self._file_downloaded.append(ftp_file)
                if signal:
                    signal.emit(ftp_file)

        self._disconnect()
        
    def _download_file(self, ftp_file: FTPFile) -> bool:
        ftp_file.mkdir()
        # TODO: 프로그레스바를 총 용량 대비로 해도 좋을 듯
        try:
            with open(ftp_file.temp_path, 'wb') as f:
                self._ftp_handler.retrbinary(
                    f'RETR {ftp_file.ftp_path}', f.write)

            shutil.move(ftp_file.temp_path, ftp_file.local_path)
            print('download file:', ftp_file.local_path)
        except Exception as e:
            print(e)
            return False
        finally:
            if os.path.exists(ftp_file.temp_path):
                os.remove(ftp_file.temp_path)

        return True

    def apply_file_to_download(self, ftp_dir: str, local_dir: str='.') -> list:
        self._connect()

        local_dir_abs = os.path.abspath(local_dir)
        self._mirror_ftp_dir(ftp_dir, local_dir)

        self._disconnect()

    def append_ftp_file(self, ftp_file: FTPFile) -> None:
        self._file_to_download.append(ftp_file)

    def _connect(self):
        if self._ftp_handler is not None:
            return

        logging.info(f'connecting {self.url}')
        self._ftp_handler = ftplib.FTP(self.url, self.username, self.password)
        self._ftp_handler.set_pasv(self._passive_mode)
        logging.info(f'connected {self.url}')

    def _disconnect(self):
        try:
            self._ftp_handler.close()
        except:
            pass
        finally:
            self._ftp_handler = None

    def _mirror_ftp_dir(self, ftp_path, local_path):
        """ replicates a directory on an ftp server recursively """
        for item in self._ftp_handler.nlst(ftp_path):
            ftp_path_item = posixpath.join(ftp_path, item)

            local_item = item.lstrip("/")
            local_path_item = os.path.join(local_path, local_item)

            if self._is_ftp_dir(ftp_path_item):
                self._mirror_ftp_dir(ftp_path_item, local_path_item)
            elif self._pattern_check(item):
                ftp_file = FTPFile(ftp_path_item, local_path_item)
                # TODO: 추가할 때 중복 제거할 수 있는 방안 고민
                logging.debug(f'Adding ftp_file: {ftp_file}')
                self._file_to_download.append(ftp_file)

    def _is_ftp_dir(self, ftp_path: str):
        """
        simply determines if an item listed on the ftp server is a
        valid directory or not
        """
        ext_size = 4
        name = os.path.basename(ftp_path)
        if len(name) >= ext_size and name[-1 * ext_size] == '.':
            return False

        original_cwd = self._ftp_handler.pwd()
        try:
            self._ftp_handler.cwd(ftp_path)
            self._ftp_handler.cwd(original_cwd)
            return True
        except ftplib.error_perm:
            return False

    def _pattern_check(self, item):
        if self.pattern is None or re.search(self.pattern, item):
            return True

        return False
