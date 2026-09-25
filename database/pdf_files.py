"""PDF files on local disk. The reports row stores the file name."""
import logging
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)


def _directory() -> Path:
    path = Path(Config.PDF_STORAGE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_name_for(user_id: int) -> str:
    return f"profile_{int(user_id)}.pdf"


def resolve(stored_name: str | None) -> Path | None:
    if not stored_name:
        return None
    # Only the file name is trusted, so a stored path cannot leave the PDF directory.
    path = _directory() / Path(stored_name).name
    if not path.is_file():
        return None
    return path


def write_pdf(user_id: int, data: bytes) -> str:
    name = file_name_for(user_id)
    dest = _directory() / name
    tmp = dest.with_suffix(".pdf.tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return name


def remove_pdf(stored_name: str | None) -> None:
    path = resolve(stored_name)
    if path is None:
        return
    try:
        path.unlink()
    except OSError:
        logger.warning("could not delete PDF %s", path)


def export_legacy_blobs(conn) -> int:
    """Copy leftover pdf_blob bytes to disk once, then clear the blob."""
    rows = conn.execute(
        """
        SELECT user_id, pdf_blob FROM reports
        WHERE pdf_blob IS NOT NULL AND length(pdf_blob) > 0
          AND (pdf_path IS NULL OR pdf_path = '')
        """
    ).fetchall()
    moved = 0
    for row in rows:
        try:
            name = write_pdf(row["user_id"], bytes(row["pdf_blob"]))
        except OSError:
            logger.exception("could not export PDF for user #%s", row["user_id"])
            continue
        conn.execute(
            "UPDATE reports SET pdf_path = ?, pdf_blob = NULL WHERE user_id = ?",
            (name, row["user_id"]),
        )
        moved += 1
    if moved:
        logger.info("Exported %d PDF blob(s) to %s", moved, Config.PDF_STORAGE_DIR)
    return moved
