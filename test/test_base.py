"""Tests for the shared AudiobookerProviderBase behaviour."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from music_assistant_models.enums import MediaType
from music_assistant_models.errors import MediaNotFoundError

from audiobooker_ma_providers._base import _author_str, _book_id, _to_audiobook


def _make_book(**kwargs):
    from audiobooker.base import AudioBook, BookAuthor, AudiobookNarrator

    defaults = dict(
        title="The Book",
        streams=["https://example.com/book.mp3"],
        authors=[BookAuthor(first_name="Jane", last_name="Doe")],
        runtime=3600,
        description="A fine book.",
        image="https://example.com/cover.jpg",
        tags=["fiction", "classic"],
    )
    defaults.update(kwargs)
    return AudioBook(**defaults)


class TestHelpers:
    def test_author_str_joins_names(self):
        book = _make_book()
        assert _author_str(book) == "Jane Doe"

    def test_author_str_defaults_unknown(self):
        book = _make_book(authors=[])
        assert _author_str(book) == "Unknown"

    def test_book_id_uses_first_stream(self):
        book = _make_book(streams=["a", "b"])
        assert _book_id(book) == "a"

    def test_book_id_falls_back_to_title(self):
        book = _make_book(streams=[], title="No Stream")
        assert _book_id(book) == "No Stream"

    def test_to_audiobook_maps_fields(self):
        book = _make_book()
        ab = _to_audiobook(book, "librivox", "librivox_1")
        assert ab.item_id == "https://example.com/book.mp3"
        assert ab.provider == "librivox"
        assert ab.name == "The Book"
        assert "Jane Doe" in ab.authors
        assert ab.duration == 3600
        assert ab.metadata.description == "A fine book."
        assert ab.metadata.genres == {"fiction", "classic"}
        mapping = next(iter(ab.provider_mappings))
        assert mapping.provider_domain == "librivox"
        assert mapping.provider_instance == "librivox_1"

    def test_to_audiobook_handles_missing_optional_fields(self):
        book = _make_book(description="", image="", tags=[])
        ab = _to_audiobook(book, "librivox", "librivox_1")
        assert ab.metadata.description is None
        assert not ab.metadata.images
        assert not ab.metadata.genres


@pytest.fixture
async def initialized_base(base_provider):
    await base_provider.handle_async_init()
    return base_provider


class TestGetAudiobook:
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_instance(self, initialized_base):
        book = _make_book()
        ab = _to_audiobook(book, initialized_base.domain, initialized_base.instance_id)
        initialized_base._cache_audiobook(ab)
        result = await initialized_base.get_audiobook(ab.item_id)
        assert result is ab

    @pytest.mark.asyncio
    async def test_cache_miss_builds_direct_stream_audiobook(self, initialized_base):
        item_id = "https://example.com/streams/mybook.mp3"
        result = await initialized_base.get_audiobook(item_id)
        assert result.item_id == item_id
        assert result.name == "mybook.mp3"

    @pytest.mark.asyncio
    async def test_cache_miss_youtube_id_uses_yt_extract(self, initialized_base):
        watch_url = "https://www.youtube.com/watch?v=abc123"
        with patch.object(
            initialized_base,
            "_yt_extract",
            return_value={"title": "YT Title", "thumbnail": "thumb.jpg", "duration": 120},
        ) as mock_extract:
            result = await initialized_base.get_audiobook(watch_url)
        mock_extract.assert_called_once_with(watch_url)
        assert result.name == "YT Title"
        assert result.duration == 120

    @pytest.mark.asyncio
    async def test_get_audiobook_not_cached_never_raises_media_not_found(self, initialized_base):
        # The base implementation always synthesizes a stub audiobook for an
        # unknown id rather than treating it as missing; document that here so
        # a future change to stricter validation is caught.
        result = await initialized_base.get_audiobook("some/unknown/id")
        assert result is not None


class TestGetStreamDetails:
    @pytest.mark.asyncio
    async def test_direct_stream_path(self, initialized_base):
        details = await initialized_base.get_stream_details(
            "https://example.com/book.mp3", MediaType.AUDIOBOOK
        )
        assert details.path == "https://example.com/book.mp3"
        assert details.provider == initialized_base.domain

    @pytest.mark.asyncio
    async def test_youtube_fallback_resolves_stream_url(self, initialized_base):
        watch_url = "https://youtu.be/abc123"
        with patch.object(
            initialized_base,
            "_yt_extract",
            return_value={"url": "https://cdn.example.com/stream.mp4"},
        ):
            details = await initialized_base.get_stream_details(watch_url, MediaType.AUDIOBOOK)
        assert details.path == "https://cdn.example.com/stream.mp4"

    @pytest.mark.asyncio
    async def test_youtube_fallback_unavailable_raises_media_not_found(self, initialized_base):
        watch_url = "https://youtu.be/abc123"
        with patch.object(initialized_base, "_yt_extract", return_value={}):
            with pytest.raises(MediaNotFoundError):
                await initialized_base.get_stream_details(watch_url, MediaType.AUDIOBOOK)

    @pytest.mark.asyncio
    async def test_yt_extract_uses_yt_dlp_and_caches(self, initialized_base):
        fake_info = {"title": "cached", "url": "https://cdn.example.com/x.mp4"}
        fake_ydl = MagicMock()
        fake_ydl.__enter__.return_value.extract_info.return_value = fake_info
        with patch("yt_dlp.YoutubeDL", return_value=fake_ydl) as mock_ydl_cls:
            first = await asyncio.to_thread(initialized_base._yt_extract, "https://youtu.be/z")
            second = await asyncio.to_thread(initialized_base._yt_extract, "https://youtu.be/z")
        assert first == fake_info
        assert second == fake_info
        # Second call must hit the cache, not yt_dlp again.
        mock_ydl_cls.assert_called_once()
