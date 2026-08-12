# bookshelf-mcp

Part of the [arr-mcps](https://github.com/SavageCore/arr-mcps) collection.
MCP server exposing [Bookshelf](https://github.com/pennydreadful/bookshelf)'s
v1 REST API (a Readarr fork, [OpenAPI 3.0.1](https://github.com/pennydreadful/bookshelf/blob/develop/src/Readarr.Api.V1/openapi.json))
as tools, so an LLM can read and manage a Bookshelf instance: authors, books,
book files, editions, series, the download queue, history, indexers, import
lists, custom formats, tags, commands, system status, and more. Full surface —
reads **and** writes, with destructive tools flagged.

Built with [FastMCP](https://gofastmcp.com).

## Getting an API key

Generate one in Bookshelf **Settings > General > Security**. Auth is the
`X-Api-Key` header.

## Install

Download a wheel from the [latest release](https://github.com/SavageCore/bookshelf-mcp/releases/latest)
and install it as a `uv` tool (no repo checkout needed):

```bash
uv tool install bookshelf_mcp-*.whl
```

This puts a `bookshelf-mcp` command on your PATH. Register it with Claude Code:

```bash
claude mcp add bookshelf \
  --env BOOKSHELF_URL=http://your-bookshelf-host:8787 \
  --env BOOKSHELF_API_KEY=<key> \
  -- bookshelf-mcp
```

### From source

```bash
uv sync
cp .env.example .env   # fill in BOOKSHELF_URL and BOOKSHELF_API_KEY
```

```bash
claude mcp add bookshelf \
  --env BOOKSHELF_URL=http://your-bookshelf-host:8787 \
  --env BOOKSHELF_API_KEY=<key> \
  -- uv run --directory /path/to/bookshelf-mcp bookshelf-mcp
```

## Config

| Env var | Required | Default |
|---|---|---|
| `BOOKSHELF_URL` | yes | - |
| `BOOKSHELF_API_KEY` | yes* | none (no `X-Api-Key` header sent if unset) |

\* Every API endpoint requires auth; practically you must set it, but the
server still starts without one so errors surface from the API rather than at
startup.

## Tools

One tool per Bookshelf v1 JSON endpoint (plus `GET /ping`). Naming is
`bookshelf_<verb>_<resource>`. GET endpoints are read-only; POST/PUT are writes;
DELETE endpoints are flagged destructive.

| Tool | Method | Endpoint |
|---|---|---|
| **Author** | | |
| `bookshelf_list_author` | GET | `/api/v1/author` |
| `bookshelf_get_author` | GET | `/api/v1/author/{id}` |
| `bookshelf_create_author` | POST | `/api/v1/author` |
| `bookshelf_update_author` | PUT | `/api/v1/author/{id}` |
| `bookshelf_delete_author` | DELETE | `/api/v1/author/{id}` |
| `bookshelf_bulk_update_author` | PUT | `/api/v1/author/editor` |
| `bookshelf_bulk_delete_author` | DELETE | `/api/v1/author/editor` |
| `bookshelf_lookup_author` | GET | `/api/v1/author/lookup` |
| **Backup** | | |
| `bookshelf_list_system_backup` | GET | `/api/v1/system/backup` |
| `bookshelf_restore_backup_upload` | POST | `/api/v1/system/backup/restore/upload` |
| `bookshelf_restore_backup` | POST | `/api/v1/system/backup/restore/{id}` |
| `bookshelf_delete_system_backup` | DELETE | `/api/v1/system/backup/{id}` |
| **Blocklist** | | |
| `bookshelf_list_blocklist` | GET | `/api/v1/blocklist` |
| `bookshelf_bulk_delete_blocklist` | DELETE | `/api/v1/blocklist/bulk` |
| `bookshelf_delete_blocklist` | DELETE | `/api/v1/blocklist/{id}` |
| **Book** | | |
| `bookshelf_list_book` | GET | `/api/v1/book` |
| `bookshelf_get_book` | GET | `/api/v1/book/{id}` |
| `bookshelf_get_book_overview` | GET | `/api/v1/book/{id}/overview` |
| `bookshelf_create_book` | POST | `/api/v1/book` |
| `bookshelf_update_book` | PUT | `/api/v1/book/{id}` |
| `bookshelf_delete_book` | DELETE | `/api/v1/book/{id}` |
| `bookshelf_update_books_monitored` | PUT | `/api/v1/book/monitor` |
| `bookshelf_bulk_update_book` | PUT | `/api/v1/book/editor` |
| `bookshelf_bulk_delete_book` | DELETE | `/api/v1/book/editor` |
| `bookshelf_lookup_book` | GET | `/api/v1/book/lookup` |
| **BookFile** | | |
| `bookshelf_list_bookfile` | GET | `/api/v1/bookfile` |
| `bookshelf_get_bookfile` | GET | `/api/v1/bookfile/{id}` |
| `bookshelf_update_bookfile` | PUT | `/api/v1/bookfile/{id}` |
| `bookshelf_delete_bookfile` | DELETE | `/api/v1/bookfile/{id}` |
| `bookshelf_bulk_update_bookfile` | PUT | `/api/v1/bookfile/editor` |
| `bookshelf_bulk_delete_bookfile` | DELETE | `/api/v1/bookfile/bulk` |
| **Bookshelf** | | |
| `bookshelf_add_books_to_shelf` | POST | `/api/v1/bookshelf` |
| **Calendar** | | |
| `bookshelf_list_calendar` | GET | `/api/v1/calendar` |
| `bookshelf_get_calendar` | GET | `/api/v1/calendar/{id}` |
| **Command** | | |
| `bookshelf_run_command` | POST | `/api/v1/command` |
| `bookshelf_list_command` | GET | `/api/v1/command` |
| `bookshelf_delete_command` | DELETE | `/api/v1/command/{id}` |
| `bookshelf_get_command` | GET | `/api/v1/command/{id}` |
| **Config** | | |
| `bookshelf_get_config_host` | GET | `/api/v1/config/host` |
| `bookshelf_update_config_host` | PUT | `/api/v1/config/host/{id}` |
| `bookshelf_get_config_host_by_id` | GET | `/api/v1/config/host/{id}` |
| `bookshelf_get_config_ui` | GET | `/api/v1/config/ui` |
| `bookshelf_update_config_ui` | PUT | `/api/v1/config/ui/{id}` |
| `bookshelf_get_config_ui_by_id` | GET | `/api/v1/config/ui/{id}` |
| `bookshelf_get_config_indexer` | GET | `/api/v1/config/indexer` |
| `bookshelf_update_config_indexer` | PUT | `/api/v1/config/indexer/{id}` |
| `bookshelf_get_config_indexer_by_id` | GET | `/api/v1/config/indexer/{id}` |
| `bookshelf_get_config_downloadclient` | GET | `/api/v1/config/downloadclient` |
| `bookshelf_update_config_downloadclient` | PUT | `/api/v1/config/downloadclient/{id}` |
| `bookshelf_get_config_downloadclient_by_id` | GET | `/api/v1/config/downloadclient/{id}` |
| `bookshelf_get_config_mediamanagement` | GET | `/api/v1/config/mediamanagement` |
| `bookshelf_update_config_mediamanagement` | PUT | `/api/v1/config/mediamanagement/{id}` |
| `bookshelf_get_config_mediamanagement_by_id` | GET | `/api/v1/config/mediamanagement/{id}` |
| `bookshelf_get_config_metadataprovider` | GET | `/api/v1/config/metadataprovider` |
| `bookshelf_update_config_metadataprovider` | PUT | `/api/v1/config/metadataprovider/{id}` |
| `bookshelf_get_config_metadataprovider_by_id` | GET | `/api/v1/config/metadataprovider/{id}` |
| `bookshelf_get_config_naming` | GET | `/api/v1/config/naming` |
| `bookshelf_get_config_naming_examples` | GET | `/api/v1/config/naming/examples` |
| `bookshelf_update_config_naming` | PUT | `/api/v1/config/naming/{id}` |
| `bookshelf_get_config_naming_by_id` | GET | `/api/v1/config/naming/{id}` |
| `bookshelf_get_config_development` | GET | `/api/v1/config/development` |
| `bookshelf_update_config_development` | PUT | `/api/v1/config/development/{id}` |
| `bookshelf_get_config_development_by_id` | GET | `/api/v1/config/development/{id}` |
| **CustomFilter** | | |
| `bookshelf_list_customfilter` | GET | `/api/v1/customfilter` |
| `bookshelf_create_customfilter` | POST | `/api/v1/customfilter` |
| `bookshelf_update_customfilter` | PUT | `/api/v1/customfilter/{id}` |
| `bookshelf_delete_customfilter` | DELETE | `/api/v1/customfilter/{id}` |
| `bookshelf_get_customfilter` | GET | `/api/v1/customfilter/{id}` |
| **CustomFormat** | | |
| `bookshelf_list_customformat` | GET | `/api/v1/customformat` |
| `bookshelf_create_customformat` | POST | `/api/v1/customformat` |
| `bookshelf_get_customformat_schema` | GET | `/api/v1/customformat/schema` |
| `bookshelf_update_customformat` | PUT | `/api/v1/customformat/{id}` |
| `bookshelf_delete_customformat` | DELETE | `/api/v1/customformat/{id}` |
| `bookshelf_get_customformat` | GET | `/api/v1/customformat/{id}` |
| **Cutoff** | | |
| `bookshelf_list_wanted_cutoff` | GET | `/api/v1/wanted/cutoff` |
| `bookshelf_get_wanted_cutoff` | GET | `/api/v1/wanted/cutoff/{id}` |
| **DelayProfile** | | |
| `bookshelf_list_delayprofile` | GET | `/api/v1/delayprofile` |
| `bookshelf_create_delayprofile` | POST | `/api/v1/delayprofile` |
| `bookshelf_reorder_delayprofile` | PUT | `/api/v1/delayprofile/reorder/{id}` |
| `bookshelf_delete_delayprofile` | DELETE | `/api/v1/delayprofile/{id}` |
| `bookshelf_update_delayprofile` | PUT | `/api/v1/delayprofile/{id}` |
| `bookshelf_get_delayprofile` | GET | `/api/v1/delayprofile/{id}` |
| **DiskSpace** | | |
| `bookshelf_get_diskspace` | GET | `/api/v1/diskspace` |
| **DownloadClient** | | |
| `bookshelf_list_downloadclient` | GET | `/api/v1/downloadclient` |
| `bookshelf_create_downloadclient` | POST | `/api/v1/downloadclient` |
| `bookshelf_action_downloadclient` | POST | `/api/v1/downloadclient/action/{name}` |
| `bookshelf_bulk_update_downloadclient` | PUT | `/api/v1/downloadclient/bulk` |
| `bookshelf_bulk_delete_downloadclient` | DELETE | `/api/v1/downloadclient/bulk` |
| `bookshelf_get_downloadclient_schema` | GET | `/api/v1/downloadclient/schema` |
| `bookshelf_test_downloadclient` | POST | `/api/v1/downloadclient/test` |
| `bookshelf_test_all_downloadclient` | POST | `/api/v1/downloadclient/testall` |
| `bookshelf_update_downloadclient` | PUT | `/api/v1/downloadclient/{id}` |
| `bookshelf_delete_downloadclient` | DELETE | `/api/v1/downloadclient/{id}` |
| `bookshelf_get_downloadclient` | GET | `/api/v1/downloadclient/{id}` |
| **Edition** | | |
| `bookshelf_list_edition` | GET | `/api/v1/edition` |
| **FileSystem** | | |
| `bookshelf_list_filesystem` | GET | `/api/v1/filesystem` |
| `bookshelf_list_filesystem_mediafiles` | GET | `/api/v1/filesystem/mediafiles` |
| `bookshelf_list_filesystem_type` | GET | `/api/v1/filesystem/type` |
| **Health** | | |
| `bookshelf_get_health` | GET | `/api/v1/health` |
| **History** | | |
| `bookshelf_list_history` | GET | `/api/v1/history` |
| `bookshelf_mark_history_failed` | POST | `/api/v1/history/failed/{id}` |
| `bookshelf_list_history_author` | GET | `/api/v1/history/author` |
| `bookshelf_list_history_since` | GET | `/api/v1/history/since` |
| **ImportList** | | |
| `bookshelf_list_importlist` | GET | `/api/v1/importlist` |
| `bookshelf_create_importlist` | POST | `/api/v1/importlist` |
| `bookshelf_action_importlist` | POST | `/api/v1/importlist/action/{name}` |
| `bookshelf_bulk_update_importlist` | PUT | `/api/v1/importlist/bulk` |
| `bookshelf_bulk_delete_importlist` | DELETE | `/api/v1/importlist/bulk` |
| `bookshelf_get_importlist_schema` | GET | `/api/v1/importlist/schema` |
| `bookshelf_test_importlist` | POST | `/api/v1/importlist/test` |
| `bookshelf_test_all_importlist` | POST | `/api/v1/importlist/testall` |
| `bookshelf_update_importlist` | PUT | `/api/v1/importlist/{id}` |
| `bookshelf_delete_importlist` | DELETE | `/api/v1/importlist/{id}` |
| `bookshelf_get_importlist` | GET | `/api/v1/importlist/{id}` |
| **ImportListExclusion** | | |
| `bookshelf_list_importlistexclusion` | GET | `/api/v1/importlistexclusion` |
| `bookshelf_create_importlistexclusion` | POST | `/api/v1/importlistexclusion` |
| `bookshelf_update_importlistexclusion` | PUT | `/api/v1/importlistexclusion/{id}` |
| `bookshelf_delete_importlistexclusion` | DELETE | `/api/v1/importlistexclusion/{id}` |
| `bookshelf_get_importlistexclusion` | GET | `/api/v1/importlistexclusion/{id}` |
| **Indexer** | | |
| `bookshelf_list_indexer` | GET | `/api/v1/indexer` |
| `bookshelf_create_indexer` | POST | `/api/v1/indexer` |
| `bookshelf_action_indexer` | POST | `/api/v1/indexer/action/{name}` |
| `bookshelf_bulk_update_indexer` | PUT | `/api/v1/indexer/bulk` |
| `bookshelf_bulk_delete_indexer` | DELETE | `/api/v1/indexer/bulk` |
| `bookshelf_get_indexer_schema` | GET | `/api/v1/indexer/schema` |
| `bookshelf_test_indexer` | POST | `/api/v1/indexer/test` |
| `bookshelf_test_all_indexer` | POST | `/api/v1/indexer/testall` |
| `bookshelf_update_indexer` | PUT | `/api/v1/indexer/{id}` |
| `bookshelf_delete_indexer` | DELETE | `/api/v1/indexer/{id}` |
| `bookshelf_get_indexer` | GET | `/api/v1/indexer/{id}` |
| **IndexerFlag** | | |
| `bookshelf_get_indexerflag` | GET | `/api/v1/indexerflag` |
| **Language** | | |
| `bookshelf_list_language` | GET | `/api/v1/language` |
| `bookshelf_get_language` | GET | `/api/v1/language/{id}` |
| **Localization** | | |
| `bookshelf_get_localization` | GET | `/api/v1/localization` |
| **Log** | | |
| `bookshelf_list_log` | GET | `/api/v1/log` |
| **LogFile** | | |
| `bookshelf_list_log_file` | GET | `/api/v1/log/file` |
| **ManualImport** | | |
| `bookshelf_list_manualimport` | GET | `/api/v1/manualimport` |
| `bookshelf_commit_manual_import` | POST | `/api/v1/manualimport` |
| **MediaManagementConfig** | | |
| `bookshelf_get_config_mediamanagement` | GET | `/api/v1/config/mediamanagement` |
| `bookshelf_update_config_mediamanagement` | PUT | `/api/v1/config/mediamanagement/{id}` |
| `bookshelf_get_config_mediamanagement_by_id` | GET | `/api/v1/config/mediamanagement/{id}` |
| **Metadata** | | |
| `bookshelf_list_metadata` | GET | `/api/v1/metadata` |
| `bookshelf_create_metadata` | POST | `/api/v1/metadata` |
| `bookshelf_action_metadata` | POST | `/api/v1/metadata/action/{name}` |
| `bookshelf_get_metadata_schema` | GET | `/api/v1/metadata/schema` |
| `bookshelf_test_metadata` | POST | `/api/v1/metadata/test` |
| `bookshelf_test_all_metadata` | POST | `/api/v1/metadata/testall` |
| `bookshelf_update_metadata` | PUT | `/api/v1/metadata/{id}` |
| `bookshelf_delete_metadata` | DELETE | `/api/v1/metadata/{id}` |
| `bookshelf_get_metadata` | GET | `/api/v1/metadata/{id}` |
| **MetadataProfile** | | |
| `bookshelf_list_metadataprofile` | GET | `/api/v1/metadataprofile` |
| `bookshelf_create_metadataprofile` | POST | `/api/v1/metadataprofile` |
| `bookshelf_get_metadataprofile_schema` | GET | `/api/v1/metadataprofile/schema` |
| `bookshelf_delete_metadataprofile` | DELETE | `/api/v1/metadataprofile/{id}` |
| `bookshelf_update_metadataprofile` | PUT | `/api/v1/metadataprofile/{id}` |
| `bookshelf_get_metadataprofile` | GET | `/api/v1/metadataprofile/{id}` |
| **Missing** | | |
| `bookshelf_list_wanted_missing` | GET | `/api/v1/wanted/missing` |
| `bookshelf_get_wanted_missing` | GET | `/api/v1/wanted/missing/{id}` |
| **Notification** | | |
| `bookshelf_list_notification` | GET | `/api/v1/notification` |
| `bookshelf_create_notification` | POST | `/api/v1/notification` |
| `bookshelf_action_notification` | POST | `/api/v1/notification/action/{name}` |
| `bookshelf_get_notification_schema` | GET | `/api/v1/notification/schema` |
| `bookshelf_test_notification` | POST | `/api/v1/notification/test` |
| `bookshelf_test_all_notification` | POST | `/api/v1/notification/testall` |
| `bookshelf_update_notification` | PUT | `/api/v1/notification/{id}` |
| `bookshelf_delete_notification` | DELETE | `/api/v1/notification/{id}` |
| `bookshelf_get_notification` | GET | `/api/v1/notification/{id}` |
| **Parse** | | |
| `bookshelf_get_parse` | GET | `/api/v1/parse` |
| **Ping** | | |
| `bookshelf_ping` | GET | `/ping` |
| **QualityDefinition** | | |
| `bookshelf_list_qualitydefinition` | GET | `/api/v1/qualitydefinition` |
| `bookshelf_update_quality_definitions` | PUT | `/api/v1/qualitydefinition/update` |
| `bookshelf_update_qualitydefinition` | PUT | `/api/v1/qualitydefinition/{id}` |
| `bookshelf_get_qualitydefinition` | GET | `/api/v1/qualitydefinition/{id}` |
| **QualityProfile** | | |
| `bookshelf_list_qualityprofile` | GET | `/api/v1/qualityprofile` |
| `bookshelf_create_qualityprofile` | POST | `/api/v1/qualityprofile` |
| `bookshelf_get_qualityprofile_schema` | GET | `/api/v1/qualityprofile/schema` |
| `bookshelf_delete_qualityprofile` | DELETE | `/api/v1/qualityprofile/{id}` |
| `bookshelf_update_qualityprofile` | PUT | `/api/v1/qualityprofile/{id}` |
| `bookshelf_get_qualityprofile` | GET | `/api/v1/qualityprofile/{id}` |
| **Queue** | | |
| `bookshelf_list_queue` | GET | `/api/v1/queue` |
| `bookshelf_bulk_delete_queue` | DELETE | `/api/v1/queue/bulk` |
| `bookshelf_delete_queue` | DELETE | `/api/v1/queue/{id}` |
| **QueueAction** | | |
| `bookshelf_grab_queue_bulk` | POST | `/api/v1/queue/grab/bulk` |
| `bookshelf_grab_queue_item` | POST | `/api/v1/queue/grab/{id}` |
| **QueueDetails** | | |
| `bookshelf_get_queue_details` | GET | `/api/v1/queue/details` |
| **QueueStatus** | | |
| `bookshelf_get_queue_status` | GET | `/api/v1/queue/status` |
| **Release** | | |
| `bookshelf_search_releases` | POST | `/api/v1/release` |
| `bookshelf_list_release` | GET | `/api/v1/release` |
| **ReleaseProfile** | | |
| `bookshelf_list_releaseprofile` | GET | `/api/v1/releaseprofile` |
| `bookshelf_create_releaseprofile` | POST | `/api/v1/releaseprofile` |
| `bookshelf_delete_releaseprofile` | DELETE | `/api/v1/releaseprofile/{id}` |
| `bookshelf_update_releaseprofile` | PUT | `/api/v1/releaseprofile/{id}` |
| `bookshelf_get_releaseprofile` | GET | `/api/v1/releaseprofile/{id}` |
| **ReleasePush** | | |
| `bookshelf_push_release` | POST | `/api/v1/release/push` |
| **RemotePathMapping** | | |
| `bookshelf_list_remotepathmapping` | GET | `/api/v1/remotepathmapping` |
| `bookshelf_create_remotepathmapping` | POST | `/api/v1/remotepathmapping` |
| `bookshelf_delete_remotepathmapping` | DELETE | `/api/v1/remotepathmapping/{id}` |
| `bookshelf_update_remotepathmapping` | PUT | `/api/v1/remotepathmapping/{id}` |
| `bookshelf_get_remotepathmapping` | GET | `/api/v1/remotepathmapping/{id}` |
| **RenameBook** | | |
| `bookshelf_get_rename` | GET | `/api/v1/rename` |
| **RetagBook** | | |
| `bookshelf_get_retag` | GET | `/api/v1/retag` |
| **RootFolder** | | |
| `bookshelf_list_rootfolder` | GET | `/api/v1/rootfolder` |
| `bookshelf_create_rootfolder` | POST | `/api/v1/rootfolder` |
| `bookshelf_delete_rootfolder` | DELETE | `/api/v1/rootfolder/{id}` |
| `bookshelf_get_rootfolder` | GET | `/api/v1/rootfolder/{id}` |
| **Search** | | |
| `bookshelf_search` | GET | `/api/v1/search` |
| **Series** | | |
| `bookshelf_list_series` | GET | `/api/v1/series` |
| **System** | | |
| `bookshelf_get_system_status` | GET | `/api/v1/system/status` |
| `bookshelf_restart` | POST | `/api/v1/system/restart` |
| `bookshelf_shutdown` | POST | `/api/v1/system/shutdown` |
| `bookshelf_get_system_routes` | GET | `/api/v1/system/routes` |
| `bookshelf_get_system_routes_duplicate` | GET | `/api/v1/system/routes/duplicate` |
| **Tag** | | |
| `bookshelf_list_tag` | GET | `/api/v1/tag` |
| `bookshelf_create_tag` | POST | `/api/v1/tag` |
| `bookshelf_update_tag` | PUT | `/api/v1/tag/{id}` |
| `bookshelf_delete_tag` | DELETE | `/api/v1/tag/{id}` |
| `bookshelf_get_tag` | GET | `/api/v1/tag/{id}` |
| **TagDetails** | | |
| `bookshelf_list_tag_detail` | GET | `/api/v1/tag/detail` |
| `bookshelf_get_tag_detail` | GET | `/api/v1/tag/detail/{id}` |
| **Task** | | |
| `bookshelf_get_system_task` | GET | `/api/v1/system/task` |
| `bookshelf_get_system_task_by_id` | GET | `/api/v1/system/task/{id}` |
| **Update** | | |
| `bookshelf_list_update` | GET | `/api/v1/update` |
| **UpdateLogFile** | | |
| `bookshelf_list_log_file_update` | GET | `/api/v1/log/file/update` |

Endpoints excluded on purpose: `/login`, `/logout`, `/api` (swagger metadata),
static web routes, the `.ics` calendar feed, and binary/text content endpoints
(media covers, raw log file contents) — `_req` JSON-decodes every response.

For POST/PUT tools, the request body is passed as a single `body` object (or
`body` list for array-bodied endpoints); query/path params are explicit
arguments. Optional params are omitted when unset so the API's defaults apply.

## Development

```bash
make help  # list all commands
```

| Command | Does |
|---|---|
| `make sync` | `uv sync` |
| `make test` | Offline tests - one per endpoint, mocked HTTP |
| `make test-integration` | Tests against the live instance (needs `BOOKSHELF_URL`/`BOOKSHELF_API_KEY`) |
| `make build` | Build wheel + sdist into `dist/` |
| `make bump-patch` / `bump-minor` / `bump-major` | Bump the version in `pyproject.toml` + `uv.lock` |
| `make clean` | Remove build artifacts |

The release workflow (`.github/workflows/release.yml`) builds and publishes to
[Releases](https://github.com/SavageCore/bookshelf-mcp/releases) whenever a `v*`
tag is pushed - so the usual flow is `make bump-patch`, commit, then tag and
push.

The integration suite is read-only by default (GET endpoints only). Set
`BOOKSHELF_WRITE_TESTS=1` to also exercise POST/PUT/DELETE against a scratch tag
(created, updated, then deleted). Never run write tests against a production
library.
