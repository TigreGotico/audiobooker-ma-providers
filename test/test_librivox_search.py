"""Representative source-level test: search and library listing map
audiobooker results into SearchResults/Audiobook objects correctly."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from music_assistant_models.enums import MediaType

from audiobooker_ma_providers.librivox import LibrivoxProvider, SUPPORTED_FEATURES


def _make_book(title, url):
    from audiobooker.base import AudioBook, BookAuthor

    return AudioBook(
        title=title,
        streams=[url],
        authors=[BookAuthor(first_name="Anon", last_name="")],
    )


@pytest.fixture
async def provider():
    manifest = SimpleNamespace(domain="librivox", type="music")
    config = SimpleNamespace(instance_id="librivox_1")
    prov = LibrivoxProvider(mass=None, manifest=manifest, config=config, supported_features=SUPPORTED_FEATURES)
    await prov.handle_async_init()
    return prov


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_maps_results_to_audiobooks(self, provider):
        books = [_make_book("Book One", "url1"), _make_book("Book Two", "url2")]
        fake_source = MagicMock()
        fake_source.search.return_value = iter(books)
        with patch("audiobooker_ma_providers.librivox._get_source", return_value=fake_source):
            result = await provider.search("anything", [MediaType.AUDIOBOOK], limit=10)
        assert [b.name for b in result.audiobooks] == ["Book One", "Book Two"]

    @pytest.mark.asyncio
    async def test_search_ignores_non_audiobook_media_types(self, provider):
        result = await provider.search("anything", [MediaType.TRACK], limit=10)
        assert result.audiobooks == []

    @pytest.mark.asyncio
    async def test_search_deduplicates_and_respects_limit(self, provider):
        books = [_make_book("A", "u1"), _make_book("A dup", "u1"), _make_book("B", "u2")]
        fake_source = MagicMock()
        fake_source.search.return_value = iter(books)
        with patch("audiobooker_ma_providers.librivox._get_source", return_value=fake_source):
            result = await provider.search("q", [MediaType.AUDIOBOOK], limit=1)
        assert len(result.audiobooks) == 1


class TestLibrary:
    @pytest.mark.asyncio
    async def test_get_library_audiobooks_uses_popular_when_available(self, provider):
        books = [_make_book("A", "u1")]
        fake_source = MagicMock()
        fake_source.iterate_popular.return_value = iter(books)
        with patch("audiobooker_ma_providers.librivox._get_source", return_value=fake_source):
            results = [ab async for ab in provider.get_library_audiobooks()]
        assert len(results) == 1
        assert results[0].name == "A"

    @pytest.mark.asyncio
    async def test_get_library_audiobooks_returns_empty_on_error(self, provider):
        fake_source = MagicMock()
        fake_source.iterate_popular.side_effect = RuntimeError("boom")
        with patch("audiobooker_ma_providers.librivox._get_source", return_value=fake_source):
            results = [ab async for ab in provider.get_library_audiobooks()]
        assert results == []
