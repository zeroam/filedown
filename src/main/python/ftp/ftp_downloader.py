import os
import re
import sys
import yaml
import gzip
import ftplib
import shutil
import tarfile
import zipfile
import logging
import subprocess
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta

from ftp.ftp_manager import FtpManager
from ftp.util import get_cfg


# global variables
logger = None
ftp_logger = None


def add_day(remote_dir, day_str):
    if remote_dir.startswith('/'):
        return f'/{day_str}{remote_dir}'
    else:
        return f'/{day_str}/{remote_dir}'


def extract_gzip(dir_path):
    for root, _, files in os.walk(dir_path): 
        for name in files:
            if not name.endswith('.gz'):
                continue
            gzip_file = os.path.join(root, name)
            h5_file = gzip_file.rstrip('.gz')
            with gzip.open(gzip_file, 'rb') as gz_f, open(h5_file, 'wb') as h5_f:
                shutil.copyfileobj(gz_f, h5_f)
            os.remove(gzip_file)


def run_shell_command(command_line):
    logging.info(f'Subprocess {" ".join(command_line)}')

    result = subprocess.run(
        command_line,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        if result.stderr:
            logger.error(f'Exception occured: {result.stderr}')
        logger.debug('Subprocess failed')
        return False

    logger.info(result.stdout)
    logger.debug('Subprocess success')
    return True


def set_logger():
    global logger
    global ftp_logger

    # logger setting
    today_str = datetime.now().strftime('%Y%m%d')
    log_dir = os.path.join(os.curdir, 'log')
    log_file = os.path.join(log_dir, f'{today_str}.log')
    parent_dir = Path(log_dir)
    parent_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file)
    #fh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(message)s',
    #     datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # remove existing handler
    for h in logger.handlers:
        logger.removeHandler(h)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    ftp_logger = logging.getLogger('ftp_manager')
    #ftp_logger.setLevel(logging.INFO)
    ftp_logger.addHandler(fh)


def download(ftp_cfg, console=None):
    # initialize
    set_logger()

    ftp_cfg_origin = ftp_cfg
    ftp_cfg = ftp_cfg.copy()

    # download day_before data
    if ftp_cfg['day_before']:
        day_before = datetime.now() - timedelta(days=ftp_cfg['day_before'])
        day_before_str = day_before.strftime('%Y%m%d')
        ftp_cfg['base_dir'] = os.path.join(ftp_cfg['base_dir'], day_before_str)
        ftp_cfg['remote_dirs'] = list(map(lambda x: add_day(x, day_before_str), ftp_cfg['remote_dirs']))

    # check download_list.txt file
    download_list_file = 'download_list.txt'
    if os.path.exists(download_list_file):
        with open(download_list_file, 'r') as r:
            for line in r:
                if day_before_str in line:
                    # 다운받은 파일 덮어쓸지 여부 물어보는 창 띄우기
                    logger.info(f"already downloaded file {ftp_cfg['base_dir']}")
                    # return 

    ftp_manager = FtpManager(**ftp_cfg)
    ftp_manager.download_ftp_tree(console)

    # move file to network directory
    if not os.path.exists(ftp_cfg['dest_dir']):
        os.makedirs(ftp_cfg['dest_dir'])
    basename = os.path.basename(ftp_cfg['base_dir'])
    dest_dir = os.path.join(ftp_cfg['dest_dir'], basename)
    if os.path.exists(dest_dir):
        logger.debug(f'already exist {dest_dir} removing...')
        shutil.rmtree(dest_dir)
    shutil.move(ftp_cfg['base_dir'], ftp_cfg['dest_dir'], copy_function=shutil.copytree)
    logger.debug(f"move file {ftp_cfg['base_dir']} to {dest_dir} complete")

    with open(download_list_file, 'a') as f:
        f.write(f"{dest_dir}\n")
