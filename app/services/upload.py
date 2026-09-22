# File upload handling and validation service.

import logging
import os
from pathlib import Path
from typing import Any, Dict, List
from werkzeug.utils import secure_filename
from app.services.preprocess import load_and_anonymize

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".csv", ".json"}


def save_and_parse_upload(file_storage, target_dir: str = "instance/uploads") -> List[Dict[str, Any]]:
    """Save an incoming uploaded file, validate format, and parse records.

    Args:
        file_storage: Werkzeug FileStorage instance.
        target_dir: Destination upload directory.

    Returns:
        List of preprocessed and anonymized complaint records.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided in upload request.")

    filename = secure_filename(file_storage.filename)
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type '{extension}'. Only .csv and .json are accepted.")

    dest_folder = Path(target_dir)
    dest_folder.mkdir(parents=True, exist_ok=True)
    saved_path = dest_folder / filename
    file_storage.save(str(saved_path))

    logger.info("Saved uploaded file to %s. Beginning anonymization and parsing.", saved_path)
    records = load_and_anonymize(str(saved_path))
    return records
