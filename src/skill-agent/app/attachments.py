"""Persist unsupported Gemini inline attachments with safe, idempotent naming."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path

from google.adk.models.llm_request import LlmRequest
from google.genai import types

try:
    from . import config
except ImportError:
    import config

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = ".attachment-manifest.json"
MAX_COLLISION_ATTEMPTS = 10_000
HASH_PREFIX_LENGTH = 12

GEMINI_SUPPORTED_INLINE_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "text/plain",
    }
)
GEMINI_SUPPORTED_INLINE_MIME_PREFIXES = ("image/", "video/", "audio/")
UNSUPPORTED_INLINE_MIME_TO_SKILL: dict[str, str] = {
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}
UNSUPPORTED_INLINE_MIME_TO_EXTENSION: dict[str, str] = {
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
}


def is_gemini_supported_inline_mime(mime_type: str | None) -> bool:
    if not mime_type:
        return False
    if mime_type in GEMINI_SUPPORTED_INLINE_MIME_TYPES:
        return True
    return mime_type.startswith(GEMINI_SUPPORTED_INLINE_MIME_PREFIXES)


def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extension_for_blob(blob: types.Blob) -> str:
    if blob.display_name and Path(blob.display_name).suffix:
        return Path(blob.display_name).suffix
    return UNSUPPORTED_INLINE_MIME_TO_EXTENSION.get(blob.mime_type or "", ".bin")


def _hash_fallback_filename(content_hash: str, suffix: str, max_length: int) -> str:
    prefix = content_hash[:HASH_PREFIX_LENGTH]
    candidate = f"{prefix}{suffix}"
    if len(candidate) <= max_length:
        return candidate
    max_prefix = max(1, max_length - len(suffix))
    return f"{prefix[:max_prefix]}{suffix}"


def cap_filename(filename: str, max_length: int) -> str:
    if len(filename) <= max_length:
        return filename

    path = Path(filename)
    suffix = path.suffix
    max_stem = max_length - len(suffix)
    if max_stem < 1:
        return filename[:max_length]
    return f"{path.stem[:max_stem]}{suffix}"


def resolve_preferred_filename(
    blob: types.Blob, max_length: int
) -> tuple[str, str, str]:
    suffix = _extension_for_blob(blob)
    if blob.display_name:
        filename = Path(blob.display_name).name
        if not Path(filename).suffix:
            filename = f"{filename}{suffix}"
    else:
        filename = f"attachment_{uuid.uuid4().hex[:8]}{suffix}"

    filename = cap_filename(filename, max_length)
    path = Path(filename)
    return filename, path.stem, path.suffix or suffix


def build_collision_filename(
    base_stem: str,
    suffix: str,
    counter: int,
    max_length: int,
    content_hash: str,
) -> str:
    candidate = f"{base_stem}_{counter}{suffix}"
    if len(candidate) <= max_length:
        return candidate

    suffix_part = f"_{counter}{suffix}"
    max_stem = max_length - len(suffix_part)
    if max_stem >= 1:
        return f"{base_stem[:max_stem]}{suffix_part}"

    return _hash_fallback_filename(content_hash, suffix, max_length)


def _load_manifest(manifest_path: Path) -> dict[str, str]:
    if not manifest_path.is_file():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Ignoring invalid attachment manifest at %s", manifest_path)
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def _save_manifest(manifest_path: Path, manifest: dict[str, str]) -> None:
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _lookup_existing_path(manifest: dict[str, str], content_hash: str) -> Path | None:
    existing = manifest.get(content_hash)
    if not existing:
        return None
    existing_path = Path(existing)
    if existing_path.is_file():
        return existing_path.resolve()
    return None


def allocate_destination(
    uploads_dir: Path,
    blob: types.Blob,
    content_hash: str,
    max_length: int,
) -> Path:
    preferred_name, base_stem, suffix = resolve_preferred_filename(blob, max_length)
    destination = uploads_dir / preferred_name
    if not destination.exists():
        return destination

    for counter in range(1, MAX_COLLISION_ATTEMPTS + 1):
        candidate_name = build_collision_filename(
            base_stem, suffix, counter, max_length, content_hash
        )
        destination = uploads_dir / candidate_name
        if not destination.exists():
            return destination

    return uploads_dir / _hash_fallback_filename(content_hash, suffix, max_length)


def save_inline_attachment(uploads_dir: Path, blob: types.Blob) -> Path:
    if not blob.data:
        display_name = blob.display_name or "attachment"
        msg = f"Attachment {display_name} has no binary data to save."
        raise ValueError(msg)

    content_hash = _content_hash(blob.data)
    max_length = config.ATTACHMENT_MAX_FILENAME_LENGTH
    manifest_path = uploads_dir / MANIFEST_FILENAME
    manifest = _load_manifest(manifest_path)

    existing_path = _lookup_existing_path(manifest, content_hash)
    if existing_path is not None:
        return existing_path

    destination = allocate_destination(uploads_dir, blob, content_hash, max_length)
    destination.write_bytes(blob.data)
    resolved = destination.resolve()
    manifest[content_hash] = str(resolved)
    _save_manifest(manifest_path, manifest)
    return resolved


def sanitize_unsupported_inline_attachments(llm_request: LlmRequest) -> None:
    """Persist unsupported attachments locally and replace them with text."""
    uploads_dir = Path(config.WORKSPACE_DIRECTORY) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    for content in llm_request.contents:
        if not content.parts:
            continue

        sanitized_parts: list[types.Part] = []
        for part in content.parts:
            inline = part.inline_data
            if (
                inline
                and inline.mime_type
                and not is_gemini_supported_inline_mime(inline.mime_type)
            ):
                saved_path = save_inline_attachment(uploads_dir, inline)
                skill_name = UNSUPPORTED_INLINE_MIME_TO_SKILL.get(inline.mime_type)
                skill_hint = (
                    f" Use the `{skill_name}` skill and `start_process` to read or modify it."
                    if skill_name
                    else " Use an appropriate skill and `start_process` to process it."
                )
                replacement_text = (
                    "[User attached file saved to workspace]\n"
                    f"Filename: {saved_path.name}\n"
                    f"Path: {saved_path}\n"
                    f"MIME type: {inline.mime_type}\n"
                    "Note: Gemini cannot read this file type directly."
                    f"{skill_hint}"
                )
                sanitized_parts.append(types.Part.from_text(text=replacement_text))
                logger.info(
                    "Replaced unsupported attachment mime_type=%s with path=%s",
                    inline.mime_type,
                    saved_path,
                )
                continue

            sanitized_parts.append(part)

        content.parts = sanitized_parts
