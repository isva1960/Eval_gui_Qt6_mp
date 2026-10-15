from pathlib import Path
from PyQt6.QtCore import QResource


def register_resources(rcc_file: str, base_dir: Path) -> bool:
    """Регистрирует файл ресурсов .rcc относительно указанной директории."""
    rcc_path = base_dir / rcc_file
    return QResource.registerResource(str(rcc_path))
