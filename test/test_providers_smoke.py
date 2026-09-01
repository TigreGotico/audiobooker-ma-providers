"""Per-source smoke tests: every provider module must import, instantiate,
and resolve through its entry point."""

from __future__ import annotations

import importlib.metadata
from types import SimpleNamespace

import pytest

PROVIDER_MODULES = {
    "librivox": "LibrivoxProvider",
    "loyalbooks": "LoyalbooksProvider",
    "darkerprojects": "DarkerprojectsProvider",
    "audioanarchy": "AudioanarchyProvider",
    "goldenaudiobooks": "GoldenaudiobooksProvider",
    "stephenkingaudiobooks": "StephenkingaudiobooksProvider",
    "hpaudiotales": "HpaudiotalesProvider",
    "thecybrarian": "ThecybrarianProvider",
    "horrorbabble": "HorrorbabbleProvider",
    "audiobooker_index": "AudiobookerIndexProvider",
}


@pytest.mark.parametrize("domain,cls_name", sorted(PROVIDER_MODULES.items()))
def test_provider_module_imports_and_exposes_class(domain, cls_name):
    module = importlib.import_module(f"audiobooker_ma_providers.{domain}")
    cls = getattr(module, cls_name)
    from audiobooker_ma_providers._base import AudiobookerProviderBase

    assert issubclass(cls, AudiobookerProviderBase)


@pytest.mark.parametrize("domain,cls_name", sorted(PROVIDER_MODULES.items()))
def test_provider_instantiates(domain, cls_name):
    module = importlib.import_module(f"audiobooker_ma_providers.{domain}")
    cls = getattr(module, cls_name)
    manifest = SimpleNamespace(domain=domain, type="music")
    config = SimpleNamespace(instance_id=f"{domain}_1")
    features = getattr(module, "SUPPORTED_FEATURES", set())
    prov = cls(mass=None, manifest=manifest, config=config, supported_features=features)
    assert prov.domain == domain
    assert prov.instance_id == f"{domain}_1"


def test_all_entry_points_resolve():
    eps = importlib.metadata.entry_points(group="music_assistant.provider")
    found = {ep.name for ep in eps}
    assert found == set(PROVIDER_MODULES)
    for ep in eps:
        module = ep.load()
        assert hasattr(module, "setup")
