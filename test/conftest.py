"""Test fixtures.

``music_assistant`` (the server package, as opposed to ``music_assistant_models``)
is not published to PyPI and cannot be installed by pip/uv. Since
``audiobooker_ma_providers`` only needs one small piece of it at import time --
``music_assistant.models.music_provider.MusicProvider`` -- a stub module that
matches the real API is injected into ``sys.modules`` before the provider
package is imported.
"""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest


def _install_music_assistant_stubs() -> None:
    if "music_assistant" in sys.modules:
        return

    ma = types.ModuleType("music_assistant")
    ma_models = types.ModuleType("music_assistant.models")
    ma_models_music_provider = types.ModuleType("music_assistant.models.music_provider")

    class Provider:
        """Minimal stand-in for music_assistant.models.provider.Provider."""

        def __init__(self, mass, manifest, config, supported_features=None):
            self.mass = mass
            self.manifest = manifest
            self.config = config
            self.supported_features = supported_features or set()

        @property
        def domain(self) -> str:
            return self.manifest.domain

        @property
        def instance_id(self) -> str:
            return self.config.instance_id

    class MusicProvider(Provider):
        """Minimal stand-in for music_assistant.models.music_provider.MusicProvider."""

    ma_models_music_provider.MusicProvider = MusicProvider

    sys.modules["music_assistant"] = ma
    sys.modules["music_assistant.models"] = ma_models
    sys.modules["music_assistant.models.music_provider"] = ma_models_music_provider


_install_music_assistant_stubs()


@pytest.fixture
def manifest():
    return SimpleNamespace(domain="librivox", type="music")


@pytest.fixture
def provider_config():
    return SimpleNamespace(instance_id="librivox_1")


@pytest.fixture
def base_provider(manifest, provider_config):
    """A bare AudiobookerProviderBase instance for exercising shared behaviour."""
    from audiobooker_ma_providers._base import AudiobookerProviderBase

    prov = AudiobookerProviderBase(mass=None, manifest=manifest, config=provider_config, supported_features=set())
    return prov
