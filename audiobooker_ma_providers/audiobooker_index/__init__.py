"""MA provider backed by the audiobooker SQLite BookIndex.

Users populate the index via CLI:
    python -m audiobooker.index build
    python -m audiobooker.index build --sources librivox loyalbooks
    python -m audiobooker.index follow-channel <youtube_url> --name "My Channel"
    python -m audiobooker.index update
"""
from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from music_assistant_models.enums import MediaType, ProviderFeature
from music_assistant_models.errors import ProviderUnavailableError
from music_assistant_models.media_items import BrowseFolder, MediaItemType, SearchResults

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

_DEFAULT_DB = Path("~/.audiobooker/index.db").expanduser()


async def setup(
    mass: MusicAssistant, manifest: ProviderManifest, config: ProviderConfig
) -> ProviderInstanceType:
    return AudiobookerIndexProvider(mass, manifest, config, SUPPORTED_FEATURES)


async def get_config_entries(
    mass: MusicAssistant,
    instance_id: str | None = None,
    action: str | None = None,
    values: dict[str, ConfigValueType] | None = None,
) -> tuple[ConfigEntry, ...]:
    return ()


class AudiobookerIndexProvider(AudiobookerProviderBase):
    """MA provider backed by the audiobooker SQLite index."""

    async def handle_async_init(self) -> None:
        await super().handle_async_init()
        try:
            from audiobooker.index import BookIndex  # noqa: PLC0415
        except ImportError as err:
            raise ProviderUnavailableError("audiobooker not installed") from err
        if not _DEFAULT_DB.exists():
            raise ProviderUnavailableError(
                f"No audiobooker index found at {_DEFAULT_DB}. "
                "Run: python -m audiobooker.index build"
            )
        self._index = BookIndex(_DEFAULT_DB)

    async def search(
        self, search_query: str, media_types: list[MediaType], limit: int = 10
    ) -> SearchResults:
        result = SearchResults()
        if MediaType.AUDIOBOOK not in media_types:
            return result

        def _do():
            hits = self._index.search_by_title(search_query, limit=limit)
            return [h.book for h in hits]

        books = await asyncio.to_thread(_do)
        result.audiobooks = [_to_audiobook(b, self.domain, self.instance_id) for b in books]
        return result

    async def browse(self, path: str) -> Sequence[MediaItemType | BrowseFolder]:
        parts = [p for p in path.split("://")[1].split("/") if p] if "://" in path else []

        if not parts:
            # Top level: show followed YouTube sources + a "All" folder
            def _get_sources():
                import sqlite3  # noqa: PLC0415
                con = sqlite3.connect(str(_DEFAULT_DB))
                con.row_factory = sqlite3.Row
                rows = con.execute("SELECT * FROM followed_sources ORDER BY name").fetchall()
                con.close()
                return rows

            try:
                rows = await asyncio.to_thread(_get_sources)
            except Exception:
                rows = []

            folders = [
                BrowseFolder(
                    item_id="all",
                    provider=self.domain,
                    path=f"{path}/all",
                    name="All Indexed Books",
                )
            ]
            for row in rows:
                folder_id = f"source_{row['id']}"
                folders.append(BrowseFolder(
                    item_id=folder_id,
                    provider=self.domain,
                    path=f"{path}/{folder_id}",
                    name=row["name"] or row["url"].split("/")[-1],
                ))
            return folders

        segment = parts[0]

        if segment == "all":
            def _do_all():
                return [h.book for h in self._index.iterate_all()][:50]
            books = await asyncio.to_thread(_do_all)
            return [_to_audiobook(b, self.domain, self.instance_id) for b in books]

        if segment.startswith("source_"):
            source_id = int(segment.split("_")[1])
            def _do_source():
                import sqlite3  # noqa: PLC0415
                con = sqlite3.connect(str(_DEFAULT_DB))
                con.row_factory = sqlite3.Row
                row = con.execute("SELECT * FROM followed_sources WHERE id=?", (source_id,)).fetchone()
                con.close()
                if not row:
                    return []
                from audiobooker.scrappers.youtube import (  # noqa: PLC0415
                    YoutubeChannelSource, YoutubePlaylistSource
                )
                import json
                tags = json.loads(row["tags"] or "[]")
                if row["kind"] == "channel":
                    src = YoutubeChannelSource(channel_url=row["url"], tags=tags)
                else:
                    src = YoutubePlaylistSource(playlist_url=row["url"], tags=tags)
                return list(src.iterate_all())[:50]

            try:
                books = await asyncio.to_thread(_do_source)
            except Exception:
                return []
            return [_to_audiobook(b, self.domain, self.instance_id) for b in books]

        return []

    async def get_library_audiobooks(self):
        def _do():
            return [h.book for h in self._index.iterate_all()]

        books = await asyncio.to_thread(_do)
        for b in books:
            yield self._cache_audiobook(_to_audiobook(b, self.domain, self.instance_id))
