import os
import re
import logging
import ftplib
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# formatter = logging.Formatter(
#     '%(asctime)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


class FtpManager:
    def __init__(self, url, base_dir, local_dirs, remote_dirs, username='anonymous', password=None,
            passive_mode=True, dir_pattern=None, pattern=None, overwrite=True, type=None, **kwargs):
        """
        Downloads an entire directory tree from an ftp server to the local destination
        :param url: ftp url address
        :param base_dir: the base directory to store the copied folder
        :param local_dirs: the local directories which in the base directory to store the copied folder each remote directries
        :param username: ftp username
        :param password: ftp password
        :param passive_mode: set ftp mode passive or active
        :param dir_pattern: Python regex pattern, only directories that match this pattern will be downloaded.
        :param pattern: Python regex pattern, only files that match this pattern will be downloaded.
        :param overwrite: set to True to force re-download of all files, even if they appear to exist already
        :param f_type: file type (kiost, noaa)
        """
        self.url = url
        self.base_dir = os.path.abspath(base_dir)
        self.local_dirs = local_dirs
        self.remote_dirs = remote_dirs
        self.username = username
        self.password = password
        self.passive_mode = passive_mode
        self.dir_pattern = dir_pattern
        self.pattern = pattern
        self.overwrite = overwrite
        self.type = type

        self.dir_success = 0
        self.dir_failed = 0
        self.file_success = 0
        self.file_exist = 0
        self.file_failed = 0
        self.connect_error = False

    def _is_ftp_dir(self, ftp_handle, name):
        """ simply determines if an item listed on the ftp server is a valid directory or not """

        # if the name has a "." in the fourth to last position, its probably a file extension
        # this is MUCH faster than trying to set every file to a working directory, and will work 99% of time
        if len(name) >= 4:
            if name[-4] == '.':
                return False

        original_cwd = ftp_handle.pwd()  # remember the current working directory
        try:
            ftp_handle.cwd(name)    # try to set directory to new name
            ftp_handle.cwd(original_cwd)    # set it back to what it is
            # check dir pattern
            if self._dir_name_match_pattern(name):
                return True
            return False
        except ftplib.error_perm:
            #logger.error(f'[FAIL] {e}')
            return False
        except Exception:
            #logger.error(f'[FAIL] {e}')
            return False

    def download_ftp_file(self, ftp_handle, local_dir, name, dest, repeat=3):
        """ downloads a single file from an ftp server """
        parent_dir = Path(os.path.join(self.base_dir, local_dir, dest))
        parent_dir.mkdir(parents=True, exist_ok=True)

        path = dest + '/' + name
        path = path.lstrip('/')
        local_path = os.path.join(parent_dir, name)
        temp_path = os.path.join(self.base_dir, str(uuid.uuid4()))

        logger.debug(f'downloading : {local_path}')
        if not os.path.exists(local_path) or self.overwrite:
            try:
                with open(temp_path, 'wb') as f:
                    global size 
                    global total_size
                    global percent

                    # ftp_callback
                    size = 0
                    percent = 0
                    total_size = ftp_handle.size(path)
                    def ftp_callback(block):
                        global size
                        global percent
                        f.write(block)
                        size += len(block)
                        percent_temp = round((size / total_size) * 100)
                        if (percent_temp - percent >= 5):
                            percent = percent_temp
                            logger.debug(f'{percent}% complete')

                    # ftp_handle.retrbinary("RETR {0}".format(path), f.write)
                    ftp_handle.retrbinary("RETR {0}".format(path), ftp_callback)
                os.rename(temp_path, local_path)
                logger.info(f'[SUCCESS] download success: {local_path}')
                self.file_success += 1
            except (FileNotFoundError, Exception) as e:
                # repeat downloading
                if repeat > 0:
                    logger.debug(f'download error in {path} repeating...')
                    self.download_ftp_file(ftp_handle, local_dir, name, dest, repeat - 1)
                else:
                    logger.error(f'[FAIL] download failed: {local_path}')
                    logger.error(f'{e}')
                    self.file_failed += 1
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            logger.debug(f'already exists: {path}')
            self.file_success += 1
            self.file_exist += 1

    def _file_name_match_pattern(self, name):
        """ returns True if filename matches the pattern """
        if self.pattern is None:
            return True
        else:
            for pattern in self.pattern:
                # 일치하는 패턴이 하나라도 있으면 True
                #logger.debug('matching {} to {}'.format(pattern, name))
                if bool(re.match(pattern, name)):
                    return True
            return False
    
    def _dir_name_match_pattern(self, name):
        """ returns True if dirname matches the pattern """
        if self.dir_pattern is None:
            return True
        else:
            for pattern in self.dir_pattern:
                if bool(re.match(pattern, name)):
                    return True
            return False

    def _mirror_ftp_dir(self, ftp_handle, local_dir, remote_dir):
        """ replicates a directory on an ftp server recursively """
        for item in ftp_handle.nlst(remote_dir):
            path = remote_dir + '/' + item
            path = path.lstrip('/')
            if self._is_ftp_dir(ftp_handle, path):
                self._mirror_ftp_dir(ftp_handle, local_dir, path)
            else:
                if self._file_name_match_pattern(item):
                    self.download_ftp_file(ftp_handle, local_dir, item, remote_dir)
                else:
                    # quietly skip the file
                    pass


    def download_ftp_tree(self, console):
        try:
            logger.debug(f'connecting {self.url}')
            if console:
                console(f'connecting {self.url}')
            ftp_handle = ftplib.FTP(self.url, self.username, self.password)
        except (IOError, Exception) as e:
            self.connect_error = True
            logger.error(f'[FAILED] {e}')
            return False, e

        # set passive mode or active mode
        ftp_handle.set_pasv(self.passive_mode)
        original_cwd = ftp_handle.pwd()
        if not os.path.exists(self.base_dir):
            Path(self.base_dir).mkdir(parents=True)

        for i in range(len(self.remote_dirs)):
            local_dir = self.local_dirs[i]
            remote_dir = self.remote_dirs[i]
            try:
                ftp_handle.cwd(remote_dir)
            except ftplib.error_perm as e:
                self.dir_failed += 1
                logger.error(f'[FAILED] {e}')
                continue

            self._mirror_ftp_dir(
                ftp_handle,
                local_dir,
                '',
            )

            ftp_handle.cwd(original_cwd)
            self.dir_success += 1
            logger.info(f'[SUCCESS] Complete FTP download for {self.url}/{remote_dir}!!')

        ftp_handle.close()
        logger.info(f'[SUCCESS] Complete FTP downloader')


if __name__ == "__main__":
    # Example usage mirroring all jpg files in an FTP directory tree.
    mysite = "ftp-npp.bou.class.noaa.gov"
    username = "anonymous"
    password = None
    remote_dir = "/20190802/JPSS-GRAN/VIIRS-Aerosol-Optical-Depth-and-Aerosol-Particle-Size-EDRs/"
    local_dir = "download"
    pattern = r".*\.xml$"
    ftp_handle = ftplib.FTP(mysite, username, password)
    manager = FtpManager(mysite, local_dir, username, password, pattern, False)
    manager.download_ftp_tree()
    print(f'file success {manager.file_success}, file failed {manager.file_failed}, file exist {manager.file_exist}')
    print(f'dir success {manager.dir_success}, dir failed {manager.dir_failed}')
