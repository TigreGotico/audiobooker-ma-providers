"""MA provider for The Cybrarian."""
from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING

from music_assistant_models.enums import MediaType, ProviderFeature
from music_assistant_models.errors import MediaNotFoundError, ProviderUnavailableError
from music_assistant_models.media_items import BrowseFolder, MediaItemType

from audiobooker_ma_providers._base import AudiobookerProviderBase, _to_audiobook, _book_id

if TYPE_CHECKING:
    from music_assistant_models.config_entries import ConfigEntry, ConfigValueType, ProviderConfig
    from music_assistant_models.provider import ProviderManifest
    from music_assistant.mass import MusicAssistant
    from music_assistant.models import ProviderInstanceType

SUPPORTED_FEATURES = {
    ProviderFeature.SEARCH,
    ProviderFeature.BROWSE,
    ProviderFeature.LIBRARY_AUDIOBOOKS,
}


async def setup(
    mass: MusicAssistant, manifest: ProviderManifest, config: ProviderConfig
) -> ProviderInstanceType:
    return ThecybrarianProvider(mass, manifest, config, SUPPORTED_FEATURES)


async def get_config_entries(
    mass: MusicAssistant,
    instance_id: str | None = None,
    action: str | None = None,
    values: dict[str, ConfigValueType] | None = None,
) -> tuple[ConfigEntry, ...]:
    return ()


def _get_source():
    from audiobooker.scrappers.youtube import TheCybrarian  # noqa: PLC0415
    return TheCybrarian()


class ThecybrarianProvider(AudiobookerProviderBase):
    """MA provider for The Cybrarian."""

    async def handle_async_init(self) -> None:
        await super().handle_async_init()
        try:
            _get_source()
        except ImportError as err:
            raise ProviderUnavailableError("audiobooker not installed") from err

    async def search(
        self, search_query: str, media_types: list[MediaType], limit: int = 10
    ) -> object:
        from music_assistant_models.media_items import SearchResults  # noqa: PLC0415
        result = SearchResults()
        if MediaType.AUDIOBOOK not in media_types:
            return result

        def _do():
            src = _get_source()
            if not hasattr(src, "search"):
                return []
            books, seen = [], set()
            for book in src.search(search_query):
                bid = _book_id(book)
                if bid not in seen:
                    seen.add(bid)
                    books.append(book)
                if len(books) >= limit:
                    break
            return books

        books = await asyncio.to_thread(_do)
        result.audiobooks = [self._cache_audiobook(_to_audiobook(b, self.domain, self.instance_id)) for b in books]
        return result

    async def browse(self, path: str) -> Sequence[MediaItemType | BrowseFolder]:
        def _do():
            src = _get_source()
            if hasattr(src, "iterate_popular"):
                return list(src.iterate_popular())[:30]
            return list(src.iterate_all())[:30]

        try:
            books = await asyncio.to_thread(_do)
        except Exception:
            return []
        return [self._cache_audiobook(_to_audiobook(b, self.domain, self.instance_id)) for b in books]

    async def get_library_audiobooks(self):
        def _do():
            src = _get_source()
            if hasattr(src, "iterate_popular"):
                return list(src.iterate_popular())[:200]
            return list(src.iterate_all())[:200]

        try:
            books = await asyncio.to_thread(_do)
        except Exception:
            books = []
        for b in books:
            yield self._cache_audiobook(_to_audiobook(b, self.domain, self.instance_id))
