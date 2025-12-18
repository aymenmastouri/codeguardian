import pytest
from codeguardian.config.settings import settings

def test_settings_loaded():
    """Verify that critical settings are loaded correctly."""
    assert settings.project_path is not None
    assert settings.inputs_path is not None
    assert settings.chroma_dir is not None

def test_paths_resolve():
    """Verify that paths are resolved to absolute paths."""
    assert settings.project_path.is_absolute()
    assert settings.inputs_path.is_absolute()
