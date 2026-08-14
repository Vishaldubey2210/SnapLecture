import shutil
from pathlib import Path


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def cleanup_directory(path: str | Path) -> None:
    directory = Path(path)

    if directory.exists():
        shutil.rmtree(directory, ignore_errors=True)


def cleanup_file(path: str | Path) -> None:
    file_path = Path(path)

    if file_path.exists() and file_path.is_file():
        file_path.unlink(missing_ok=True)