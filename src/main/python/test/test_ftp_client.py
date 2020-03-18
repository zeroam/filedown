import os
import shutil
import socket
import unittest

from ftp.ftp_client import FTPClient, FTPFile


class TestFTPClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.url = 'ftp-npp.bou.class.noaa.gov'
        cls.local_dir = 'download'

    def test_connection(self):
        ftp_client = FTPClient(self.url)
        ftp_client._connect()
        ftp_client._disconnect()

    def test_connection_invalid_url_exception(self):
        with self.assertRaises(socket.gaierror):
            ftp_client = FTPClient('wrong.url.address')
            ftp_client._connect()
            ftp_client._disconnect()

    def test_apply_file_to_download(self):
        ftp_client = FTPClient(self.url)
        remote_dir = '/20200301/ATMS-SDR/ATMS-SDR/'
        ftp_client.apply_file_to_download(remote_dir, self.local_dir)
        
        local_paths = [
            r'download\J01\ATMS-SDR_ATMS-SDR_20200301_01084.tar',
            r'download\J01\ATMS-SDR_ATMS-SDR_20200301_01084.tar.manifest.xml',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_01424.tar',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_01424.tar.manifest.xml',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_09994.tar',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_09994.tar.manifest.xml']

        ftp_paths = [
            '/20200301/ATMS-SDR/ATMS-SDR/J01/ATMS-SDR_ATMS-SDR_20200301_01084.tar',
            '/20200301/ATMS-SDR/ATMS-SDR/J01/ATMS-SDR_ATMS-SDR_20200301_01084.tar.manifest.xml',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_01424.tar',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_01424.tar.manifest.xml',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_09994.tar',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_09994.tar.manifest.xml']

        for i, ftp_file in enumerate(ftp_client.file_to_download):
            self.assertEqual(ftp_file.ftp_path, ftp_paths[i])
            self.assertEqual(ftp_file.local_path, os.path.abspath(local_paths[i]))


    def test_download_file(self):
        ftp_path = '/20200301/ATMS-SDR/ATMS-SDR/J01/ATMS-SDR_ATMS-SDR_20200301_01084.tar.manifest.xml'
        local_path = r'download\test_file'
        ftp_file = FTPFile(ftp_path, local_path)

        ftp_client = FTPClient(self.url)
        ftp_client.append_ftp_file(ftp_file)
        ftp_client.download()

        if not os.path.exists(local_path):
            raise FileNotFoundError(f'file not found: {local_path}')

    def test_download_file_already_exist(self):
        ftp_path = '/20200301/ATMS-SDR/ATMS-SDR/J01/ATMS-SDR_ATMS-SDR_20200301_01084.tar.manifest.xml'
        local_path = r'download\already_exist'
        ftp_file = FTPFile(ftp_path, local_path)

        ftp_client = FTPClient(self.url)
        ftp_client.append_ftp_file(ftp_file)
        ftp_client.download()
        ftp_client.append_ftp_file(ftp_file)
        ftp_client.download()

        if not os.path.exists(local_path):
            raise FileNotFoundError(f'file not found: {local_path}')


    def test_filelist_download(self):

        local_paths = [
            r'download\J01\ATMS-SDR_ATMS-SDR_20200301_01084.tar',
            r'download\J01\ATMS-SDR_ATMS-SDR_20200301_01084.tar.manifest.xml',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_01424.tar',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_01424.tar.manifest.xml',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_09994.tar',
            r'download\NPP\ATMS-SDR_ATMS-SDR_20200301_09994.tar.manifest.xml']

        ftp_paths = [
            '/20200301/ATMS-SDR/ATMS-SDR/J01/ATMS-SDR_ATMS-SDR_20200301_01084.tar',
            '/20200301/ATMS-SDR/ATMS-SDR/J01/ATMS-SDR_ATMS-SDR_20200301_01084.tar.manifest.xml',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_01424.tar',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_01424.tar.manifest.xml',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_09994.tar',
            '/20200301/ATMS-SDR/ATMS-SDR/NPP/ATMS-SDR_ATMS-SDR_20200301_09994.tar.manifest.xml']

        ftp_client = FTPClient(self.url)
        remote_dir = '/20200301/ATMS-SDR/ATMS-SDR/'
        ftp_client.apply_file_to_download(remote_dir, self.local_dir)
        ftp_client.download()

        # file exist check
        for local_path in local_paths:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f'file not found: {local_path}')

        # file_downloaded list check
        for i, ftp_file in enumerate(ftp_client.file_downloaded):
            self.assertEqual(ftp_file.ftp_path, ftp_paths[i])
            self.assertEqual(ftp_file.local_path, os.path.abspath(local_paths[i]))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.local_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
