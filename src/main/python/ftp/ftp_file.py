import uuid
from pathlib import Path

class FTPFile:

    def __init__(self, ftp_path: str, local_path: str):
        self._ftp_path = ftp_path
        self._local_path = Path(local_path)
        self._local_dir = self._local_path.parent
        self._temp_path = self._local_dir / str(uuid.uuid4())

    @property
    def ftp_path(self) -> str:
        return self._ftp_path

    @property
    def local_dir(self) -> str:
        return str(self._local_dir)

    @property
    def local_path(self) -> str:
        return str(self._local_path)

    @property
    def temp_path(self) -> str:
        return str(self._temp_path)

    def mkdir(self, parents=True, exist_ok=True):
        self._local_dir.mkdir(
            parents=parents, exist_ok=exist_ok)

    def __str__(self):
        return f'<FTP Path: {self.ftp_path}>'
