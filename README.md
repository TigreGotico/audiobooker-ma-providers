# audiobooker-ma-providers

This package adds free audiobook providers to [Music Assistant](https://music-assistant.io). Each public-domain audiobook catalogue registers as its own provider.

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
| `librivox` | LibriVox, volunteer-read public domain audiobooks |
| `loyalbooks` | Loyal Books, public domain audiobooks and ebooks |
| `darkerprojects` | Darker Projects, audio dramas and fiction |
| `audioanarchy` | Audio Anarchy, independent audio productions |
| `goldenaudiobooks` | Golden Audiobooks, classic literature |

| Domain | Description |
|---|---|
| `stephenkingaudiobooks` | Stephen King Audiobooks archive |
| `hpaudiotales` | H.P. Lovecraft audio tales |
| `thecybrarian` | The Cybrarian, curated free audiobooks |
| `horrorbabble` | HorrorBabble, horror fiction narrations |
| `audiobooker_index` | Aggregated index across all audiobooker sources |

## Requirements

- `music-assistant-plugin-manager`
- `audiobooker`, the audiobook catalogue and streaming client

## See also

[audiobooker-ma-provider](https://github.com/TigreGotico/audiobooker-ma-provider) is the single-source variant. Use it if you need only one provider entry.

## Part of plugin-managers

[plugin-managers](https://github.com/TigreGotico/plugin-managers) provides the entrypoint-based plugin discovery that this package uses for Music Assistant and Home Assistant.
