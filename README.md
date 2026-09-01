# audiobooker-ma-providers

This package adds free audiobook providers to [Music Assistant](https://music-assistant.io). Each source registers as its own provider, backed by the [audiobooker](https://github.com/TigreGotico/audiobooker) scraper library, so a fault or removal in one catalogue never affects the others.

## What it provides

| Domain | Source |
|---|---|
| `librivox` | LibriVox, volunteer-read public domain audiobooks |
| `loyalbooks` | Loyal Books, public domain audiobooks and ebooks |
| `darkerprojects` | Darker Projects, audio dramas and fiction |
| `audioanarchy` | Audio Anarchy, independent audio productions |
| `goldenaudiobooks` | Golden Audiobooks, classic literature |
| `stephenkingaudiobooks` | Stephen King Audiobooks archive |
| `hpaudiotales` | H.P. Lovecraft audio tales |
| `thecybrarian` | The Cybrarian, curated free audiobooks (YouTube-hosted) |
| `horrorbabble` | HorrorBabble, horror fiction narrations (YouTube-hosted) |
| `audiobooker_index` | Local SQLite index aggregating any of the sources above, plus followed YouTube channels or playlists |

## Install

Install through [music-assistant-plugin-manager](https://github.com/TigreGotico/plugin-managers):

```bash
pip install audiobooker-ma-providers
mass-pm
```

The plugin manager discovers each provider through its entry point under `music_assistant.provider` and lists it in Music Assistant's provider picker. Add one provider instance per catalogue you want; each is independent and needs no account or API key.

## Configuration

None of the providers expose configuration entries: every catalogue is scraped anonymously and needs no credentials. The one exception is `audiobooker_index`, which reads a local SQLite database instead of scraping live. Build and maintain that database with the `audiobooker` CLI before adding the provider:

```bash
python -m audiobooker.index build
python -m audiobooker.index build --sources librivox loyalbooks
python -m audiobooker.index follow <youtube_url> --name "My Channel"
python -m audiobooker.index update
```

The index lives at `~/.audiobooker/index.db`. If it does not exist yet, `audiobooker_index` refuses to start and names the command to run.

## YouTube fallback

Some catalogues host audio on YouTube instead of serving a direct file. `thecybrarian` and `horrorbabble` are YouTube-only; `audiobooker_index` can also surface YouTube results for followed channels and playlists. For those items, streaming resolves through [yt-dlp](https://github.com/yt-dlp/yt-dlp) rather than a plain HTTP URL. `yt-dlp` is a required dependency of this package: without it, every provider whose catalogue is YouTube-hosted has no way to resolve a playable stream. Resolved metadata and stream URLs are cached per watch URL for the lifetime of the provider instance to avoid re-extracting on every request.

## Limitations

- Scraping is best-effort against sites that were never built as an API; a source's page layout changing can break search or listing until `audiobooker` is updated.
- Catalogues are read-only. There is no way to upload, favorite server-side, or otherwise modify the source libraries through these providers.
- YouTube-backed streams inherit YouTube's usual throttling and regional availability; a title that plays in one region may fail in another.
- `audiobooker_index` only reflects what was indexed; it does not refresh automatically and needs the CLI commands above to stay current.

## Related projects

- [audiobooker](https://github.com/TigreGotico/audiobooker) — the scraper and streaming client this package wraps
- [audiobooker-ma-provider](https://github.com/TigreGotico/audiobooker-ma-provider) — single-source variant, for installing only one catalogue
- [plugin-managers](https://github.com/TigreGotico/plugin-managers) — the entry-point-based plugin discovery used by `mass-pm`
- [ovos-ma-player](https://github.com/TigreGotico/ovos-ma-player) — an OpenVoiceOS media player backed by Music Assistant
