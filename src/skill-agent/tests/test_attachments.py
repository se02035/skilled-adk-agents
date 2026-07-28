"""Tests for attachment sanitization and safe filename handling."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from google.adk.models.llm_request import LlmRequest
from google.genai import types

APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

import config  # noqa: E402
import attachments  # noqa: E402

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class AttachmentHelpersTest(unittest.TestCase):
    def test_build_collision_filename_uses_fixed_stem(self) -> None:
        first = attachments.build_collision_filename(
            "Template_Pure", ".pptx", 1, 200, "abc123"
        )
        second = attachments.build_collision_filename(
            "Template_Pure", ".pptx", 2, 200, "abc123"
        )
        self.assertEqual(first, "Template_Pure_1.pptx")
        self.assertEqual(second, "Template_Pure_2.pptx")

    def test_cap_filename_truncates_long_stem(self) -> None:
        long_name = "a" * 250 + ".pptx"
        capped = attachments.cap_filename(long_name, 200)
        self.assertLessEqual(len(capped), 200)
        self.assertTrue(capped.endswith(".pptx"))

    def test_build_collision_filename_falls_back_to_hash_when_too_long(self) -> None:
        long_stem = "x" * 250
        candidate = attachments.build_collision_filename(
            long_stem, ".pptx", 9999, 20, "fedcba9876543210"
        )
        self.assertLessEqual(len(candidate), 20)
        self.assertTrue(candidate.endswith(".pptx"))


class SaveInlineAttachmentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.uploads_dir = Path(self.temp_dir.name) / "uploads"
        self.uploads_dir.mkdir(parents=True)
        self.previous_workspace = config.WORKSPACE_DIRECTORY
        config.WORKSPACE_DIRECTORY = str(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        config.WORKSPACE_DIRECTORY = self.previous_workspace
        self.temp_dir.cleanup()

    def _blob(self, data: bytes, display_name: str | None = None) -> types.Blob:
        return types.Blob(
            mime_type=PPTX_MIME,
            display_name=display_name,
            data=data,
        )

    def test_same_bytes_saved_twice_reuses_path(self) -> None:
        blob = self._blob(b"same-content", "Template_Pure.pptx")
        first = attachments.save_inline_attachment(self.uploads_dir, blob)
        second = attachments.save_inline_attachment(self.uploads_dir, blob)

        self.assertEqual(first, second)
        saved_files = [
            path
            for path in self.uploads_dir.iterdir()
            if path.name != attachments.MANIFEST_FILENAME
        ]
        self.assertEqual(len(saved_files), 1)

    def test_different_bytes_use_numeric_collision_suffixes(self) -> None:
        first = attachments.save_inline_attachment(
            self.uploads_dir, self._blob(b"one", "Template_Pure.pptx")
        )
        second = attachments.save_inline_attachment(
            self.uploads_dir, self._blob(b"two", "Template_Pure.pptx")
        )

        self.assertEqual(first.name, "Template_Pure.pptx")
        self.assertEqual(second.name, "Template_Pure_1.pptx")

    def test_long_display_name_is_capped(self) -> None:
        long_name = ("VeryLongTemplateName" * 20) + ".pptx"
        saved = attachments.save_inline_attachment(
            self.uploads_dir,
            self._blob(b"long-name", long_name),
        )
        self.assertLessEqual(len(saved.name), config.ATTACHMENT_MAX_FILENAME_LENGTH)

    def test_repeated_sanitization_does_not_create_duplicates(self) -> None:
        blob = types.Blob(
            mime_type=PPTX_MIME,
            display_name="Template_Pure.pptx",
            data=b"repeat-me",
        )
        request = LlmRequest(
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text="use this template"),
                        types.Part(inline_data=blob),
                    ],
                )
            ]
        )

        for _ in range(50):
            attachments.sanitize_unsupported_inline_attachments(request)

        saved_files = [
            path
            for path in self.uploads_dir.iterdir()
            if path.name != attachments.MANIFEST_FILENAME
        ]
        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0].name, "Template_Pure.pptx")
        self.assertIn(
            "[User attached file saved to workspace]",
            request.contents[0].parts[1].text or "",
        )


if __name__ == "__main__":
    unittest.main()
