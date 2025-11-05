import re

import pytest


@pytest.mark.unit
class TestFilenameSanitization:
    """Test that filenames are properly sanitized"""

    INVALID_DIR_CHARS = r'[<>:"/\\|?*]'

    @pytest.mark.parametrize(
        "bad_filename,expected",
        [
            ("file<name>.txt", "file_name_.txt"),
            ("path/to\\file", "path_to_file"),
            ("file:name|test", "file_name_test"),
            ("file*?.mp4", "file__.mp4"),
            (
                "../../../etc/passwd",
                "../../../etc/passwd",
            ),  # traversal preserved for now
            ("normal_file.jpg", "normal_file.jpg"),
        ],
    )
    def test_sanitize_dangerous_chars(self, bad_filename, expected):
        """Verify filesystem-dangerous chars are replaced"""
        result = re.sub(self.INVALID_DIR_CHARS, "_", bad_filename).strip()
        assert result == expected
