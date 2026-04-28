# audiobooker-ma-providers

Per-source free audiobook providers for [Music Assistant](https://music-assistant.io) — each public-domain audiobook catalogue registers as its own provider.

## Install

```bash
pip install audiobooker-ma-providers
```

## Usage

```bash
mass-pm   # instead of music-assistant
```

All providers appear automatically in Music Assistant's provider list after installation.

## Provider domains

| Domain | Description |
|---|---|
| `librivox` | LibriVox — volunteer-read public domain audiobooks |
| `loyalbooks` | Loyal Books — public domain audiobooks and ebooks |
| `darkerprojects` | Darker Projects — audio dramas and fiction |
| `audioanarchy` | Audio Anarchy — independent audio productions |
| `goldenaudiobooks` | Golden Audiobooks — classic literature |
| `stephenkingaudiobooks` | Stephen King Audiobooks archive |
| `hpaudiotales` | H.P. Lovecraft audio tales |
| `thecybrarian` | The Cybrarian — curated free audiobooks |
| `horrorbabble` | HorrorBabble — horror fiction narrations |
| `audiobooker_index` | Aggregated index across all audiobooker sources |

## Requirements

- `music-assistant-plugin-manager`
- `audiobooker` — audiobook catalogue and streaming client

## See also

[audiobooker-ma-provider](https://github.com/TigreGotico/audiobooker-ma-provider) — the single-source variant if you only need one provider entry.

## Part of plugin-managers

Powered by [plugin-managers](https://github.com/TigreGotico/plugin-managers) — entrypoint-based plugin discovery for Music Assistant and Home Assistant.
