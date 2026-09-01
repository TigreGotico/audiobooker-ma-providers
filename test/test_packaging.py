"""Metadata checks: the yt_dlp dependency that _base.py imports for the
YouTube stream-resolution fallback must be declared, and audiobooker must
carry a floor pin."""

from __future__ import annotations

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _dependencies():
    data = tomllib.loads(PYPROJECT.read_text())
    return data["project"]["dependencies"]


def test_yt_dlp_is_declared():
    deps = _dependencies()
    assert any(d.startswith("yt-dlp") or d.startswith("yt_dlp") for d in deps), (
        "_base.py imports yt_dlp for the YouTube fallback stream path used by "
        "several providers (e.g. thecybrarian, horrorbabble); it must be a "
        "declared dependency, not an undeclared transitive assumption."
    )


def test_audiobooker_has_floor_pin():
    deps = _dependencies()
    audiobooker_dep = next(d for d in deps if d.split(">=")[0].split("=")[0] == "audiobooker")
    assert ">=" in audiobooker_dep, "audiobooker must carry a floor pin"


def test_license_metadata_present():
    data = tomllib.loads(PYPROJECT.read_text())
    project = data["project"]
    assert project.get("license") == "Apache-2.0"
    assert project.get("license-files") == ["LICENSE"]
    assert "classifiers" not in project
