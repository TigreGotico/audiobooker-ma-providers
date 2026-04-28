"""Shared helpers for all audiobooker MA providers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from music_assistant_models.enums import ContentType, ImageType, MediaType, StreamType
from music_assistant_models.errors import MediaNotFoundError
from music_assistant_models.media_items import (
    Audiobook,
    AudioFormat,
    MediaItemImage,
    ProviderMapping,
    UniqueList,
)
from music_assistant_models.streamdetails import StreamDetails

from music_assistant.models.music_provider import MusicProvider

if TYPE_CHECKING:
    from music_assistant_models.config_entries import ConfigEntry, ConfigValueType, ProviderConfig
    from music_assistant_models.provider import ProviderManifest
    from music_assistant.mass import MusicAssistant
    from music_assistant.models import ProviderInstanceType


def _author_str(book) -> str:
    parts = []
    for a in book.authors:
        name = f"{a.first_name} {a.last_name}".strip()
        if name:
            parts.append(name)
    return ", ".join(parts) or "Unknown"


def _book_id(book) -> str:
    return book.streams[0] if book.streams else book.title


def _to_audiobook(book, provider_domain: str, instance_id: str) -> Audiobook:
    ab = Audiobook(
        item_id=_book_id(book),
        provider=provider_domain,
        name=book.title,
        provider_mappings={
            ProviderMapping(
                item_id=_book_id(book),
                provider_domain=provider_domain,
                provider_instance=instance_id,
            )
        },
        authors=UniqueList([_author_str(book)]),
        narrators=UniqueList(
            [f"{book.narrator.first_name} {book.narrator.last_name}".strip()]
            if book.narrator and (book.narrator.first_name or book.narrator.last_name)
            else []
        ),
        duration=int(book.runtime) if book.runtime else 0,
    )
    if book.description:
        ab.metadata.description = book.description
    if book.image:
        ab.metadata.images = UniqueList([
            MediaItemImage(
                type=ImageType.THUMB,
                path=book.image,
                provider=instance_id,
                remotely_accessible=True,
            )
        ])
    if book.tags:
        ab.metadata.genres = set(book.tags)
    return ab


_YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "format": "bestaudio/best",
    "skip_download": True,
}


def _yt_extract_fresh(watch_url: str) -> dict:
    import yt_dlp  # noqa: PLC0415
    with yt_dlp.YoutubeDL(_YTDLP_OPTS) as ydl:
        return ydl.extract_info(watch_url, download=False) or {}


class AudiobookerProviderBase(MusicProvider):
    """Base class for all audiobooker MA providers."""

    @property
    def is_streaming_provider(self) -> bool:
        return True

    async def handle_async_init(self) -> None:
        self._yt_info_cache: dict[str, dict] = {}
        self._audiobook_cache: dict[str, Audiobook] = {}

    def _yt_extract(self, watch_url: str) -> dict:
        if watch_url not in self._yt_info_cache:
            self._yt_info_cache[watch_url] = _yt_extract_fresh(watch_url)
        return self._yt_info_cache[watch_url]

    def _cache_audiobook(self, ab: Audiobook) -> Audiobook:
        self._audiobook_cache[ab.item_id] = ab
        return ab

    async def get_audiobook(self, prov_audiobook_id: str) -> Audiobook:
        if prov_audiobook_id in self._audiobook_cache:
            return self._audiobook_cache[prov_audiobook_id]
        from audiobooker.base import AudioBook  # noqa: PLC0415
        if "youtube.com" in prov_audiobook_id or "youtu.be" in prov_audiobook_id:
            info = await asyncio.to_thread(self._yt_extract, prov_audiobook_id)
            book = AudioBook(
                title=info.get("title") or prov_audiobook_id,
                streams=[prov_audiobook_id],
                image=info.get("thumbnail") or "",
                authors=[],
                runtime=int(info.get("duration") or 0),
            )
        else:
            book = AudioBook(
                title=prov_audiobook_id.split("/")[-1],
                streams=[prov_audiobook_id],
                authors=[],
            )
        return _to_audiobook(book, self.domain, self.instance_id)

    async def get_stream_details(self, item_id: str, media_type: MediaType) -> StreamDetails:
        if "youtube.com" in item_id or "youtu.be" in item_id:
            info = await asyncio.to_thread(self._yt_extract, item_id)
            stream_url = info.get("url", "")
            if not stream_url:
                raise MediaNotFoundError(f"Could not resolve YouTube stream for: {item_id}")
            content_type = ContentType.MP4 if ".mp4" in stream_url else ContentType.OGG
            return StreamDetails(
                provider=self.domain,
                item_id=item_id,
                audio_format=AudioFormat(content_type=content_type),
                media_type=MediaType.AUDIOBOOK,
                stream_type=StreamType.HTTP,
                path=stream_url,
                can_seek=True,
                allow_seek=True,
            )
        return StreamDetails(
            provider=self.domain,
            item_id=item_id,
            audio_format=AudioFormat(content_type=ContentType.MP3),
            media_type=MediaType.AUDIOBOOK,
            stream_type=StreamType.HTTP,
            path=item_id,
            can_seek=True,
            allow_seek=True,
        )
