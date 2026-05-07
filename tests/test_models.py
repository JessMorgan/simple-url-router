import pytest
from pydantic import TypeAdapter

from app.models import KeyParam, PathValue

_key_adapter = TypeAdapter(KeyParam)
_path_adapter = TypeAdapter(PathValue)


class TestKeyParam:
    def test_valid_integer_string(self):
        assert _key_adapter.validate_python("42") == "42"

    def test_valid_guid(self):
        assert _key_adapter.validate_python("550e8400-e29b-41d4-a716-446655440000")

    def test_valid_alphanumeric(self):
        assert _key_adapter.validate_python("my-key_123.abc")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="path traversal"):
            _key_adapter.validate_python("../etc")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError):
            _key_adapter.validate_python("key with spaces")

    def test_rejects_long_key(self):
        with pytest.raises(ValueError):
            _key_adapter.validate_python("a" * 300)


class TestPathValue:
    def test_valid_absolute_path(self):
        assert _path_adapter.validate_python("/devices/powerspec_g757") == "/devices/powerspec_g757"

    def test_valid_nested_path(self):
        assert _path_adapter.validate_python("/a/b/c/d/e") == "/a/b/c/d/e"

    def test_rejects_relative_path(self):
        with pytest.raises(ValueError, match="Path must start with /"):
            _path_adapter.validate_python("devices/powerspec")

    def test_rejects_url_scheme(self):
        with pytest.raises(ValueError):
            _path_adapter.validate_python("http://evil.com")

        with pytest.raises(ValueError):
            _path_adapter.validate_python("https://evil.com")

    def test_rejects_protocol_relative(self):
        with pytest.raises(ValueError, match="URI scheme"):
            _path_adapter.validate_python("//evil.com")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="path traversal"):
            _path_adapter.validate_python("/devices/../etc")

    def test_rejects_control_chars(self):
        with pytest.raises(ValueError, match="control characters"):
            _path_adapter.validate_python("/devices/new\nline")
