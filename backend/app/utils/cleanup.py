from pathlib import Path
import shutil


def cleanup_directory(directory: Path) -> None:
    """
    Permanently remove a temporary processing directory.

    This function is intentionally defensive so that cleanup
    failures do not crash the API response.
    """

    try:
        directory = Path(directory)

        if directory.exists() and directory.is_dir():
            shutil.rmtree(directory, ignore_errors=True)

    except Exception:
        # Cleanup must never break an already generated response.
        pass