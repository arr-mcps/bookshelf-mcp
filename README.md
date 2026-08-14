# bookshelf-mcp

Part of the [arr-mcps](https://github.com/arr-mcps/arr-mcps) collection.
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

Download a wheel from the [latest release](https://github.com/arr-mcps/bookshelf-mcp/releases/latest)
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

**15 resource-scoped tools**, each covering multiple Bookshelf v1 endpoints
(221 total) via an `operation` parameter. Call a tool with `operation` set
to one of its listed operations and an `arguments` dict matching that
operation's parameters — the tool's own description (visible to your MCP
client) lists every operation, its signature, and a one-line doc. This keeps
the full REST surface available while costing a fraction of the context
budget of registering all 221 endpoints as separate tools.

| Tool | Operations | Kind |
|---|---|---|
| `bookshelf_profiles_formats` | 40 | reads + writes |
| `bookshelf_media_library` | 33 | reads + writes |
| `bookshelf_config` | 27 | reads + writes |
| `bookshelf_system_commands` | 20 | reads + writes |
| `bookshelf_notifications_metadata` | 18 | reads + writes |
| `bookshelf_download_clients` | 16 | reads + writes |
| `bookshelf_import_lists` | 16 | reads + writes |
| `bookshelf_indexers` | 11 | reads + writes |
| `bookshelf_storage` | 9 | reads + writes |
| `bookshelf_history_blocklist` | 7 | reads + writes |
| `bookshelf_queue` | 7 | reads + writes |
| `bookshelf_tags` | 7 | reads + writes |
| `bookshelf_wanted` | 4 | read-only |
| `bookshelf_release_search` | 4 | reads + writes |
| `bookshelf_calendar` | 2 | read-only |

Example: `bookshelf_queue(operation="bookshelf_delete_queue", arguments={"id": 42})`.
Endpoint-level naming (`bookshelf_<verb>_<resource>`) is preserved as the
`operation` value, so the full endpoint list is still discoverable from each
group tool's description at runtime.

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
[Releases](https://github.com/arr-mcps/bookshelf-mcp/releases) whenever a `v*`
tag is pushed - so the usual flow is `make bump-patch`, commit, then tag and
push.

The integration suite is read-only by default (GET endpoints only). Set
`BOOKSHELF_WRITE_TESTS=1` to also exercise POST/PUT/DELETE against a scratch tag
(created, updated, then deleted). Never run write tests against a production
library.
