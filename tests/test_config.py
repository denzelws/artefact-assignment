"""Settings checks: defaults, env overrides, and the cached accessor."""

from pathlib import Path

from emporio.config import Settings, get_settings


def _isolated(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Hermetic Settings: neither the process env nor the repo .env may leak in."""
    for var in ("EMPORIO_TEMPERATURE", "EMPORIO_OLLAMA_MODEL", "EMPORIO_MODEL_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)


def test_temperature_defaults_to_0_2(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    _isolated(monkeypatch, tmp_path)
    assert Settings().temperature == 0.2


def test_temperature_env_override(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EMPORIO_TEMPERATURE", "0.7")
    assert Settings().temperature == 0.7


def test_get_settings_is_cached() -> None:
    # No value assertions here: the real .env may leak in, and unit tests
    # must stay hermetic — identity is the property under test.
    assert get_settings() is get_settings()
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()


def test_ollama_env_prefix(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EMPORIO_OLLAMA_MODEL", "qwen2.5:7b")
    assert Settings().ollama_model == "qwen2.5:7b"


def test_ollama_model_default(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    _isolated(monkeypatch, tmp_path)
    assert Settings().ollama_model == "llama3.1:8b"
