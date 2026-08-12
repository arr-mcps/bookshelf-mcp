# AGENTS.md — bookshelf-mcp

MCP server exposing Bookshelf's v1 REST API (Readarr fork, OpenAPI 3.0.1) as tools so an LLM can read and manage a Bookshelf instance: authors, books, book files, editions, series, queue, history, indexers, import lists, custom formats, tags, commands, system status, and more. Full surface — reads and writes. Uses FastMCP, `uv` for deps.

Exposed as **15 resource-scoped portmanteau tools**, not one tool per endpoint — see "Tool registry and the spec" below. A prior version registered all 221 endpoints individually; that blew the MCP context budget (~221 tools × ~250 tokens ≈ 55k tokens just for this one server) and has been retired.

## Testing
- Offline suite: `make test` (or `uv run pytest`)
- Live integration (needs `BOOKSHELF_URL`/`BOOKSHELF_API_KEY`): `make test-integration`
  - GET endpoints run against the live instance.
  - POST/PUT/DELETE only run when `BOOKSHELF_WRITE_TESTS=1` (safe create→update→delete cycles against a scratch tag, then cleanup). Never point write tests at a production library.

## Tool registry and the spec
- `_TOOL_REGISTRY` in `bookshelf_mcp.py` is generated from the vendored spec at `tests/data/bookshelf_openapi.json` by `scripts/generate_registry.py`. It lists every JSON-producing endpoint under `/api/v1` plus `GET /ping`.
- Excluded on purpose: `/login`, `/logout`, `/api` (swagger metadata), static web routes, the `.ics` calendar feed, and binary/text endpoints (media covers, raw log files) — `_req` JSON-decodes every response.
- To add a tool or refresh coverage, edit `scripts/generate_registry.py` (add NAME_OVERRIDES/DOC_OVERRIDES) and regenerate from the vendored spec, then re-run the tests. Do not hand-edit the registry.
- Endpoint function naming (internal, no longer an MCP tool name): `bookshelf_<verb>_<resource>` derived from path + method (e.g. `bookshelf_list_author`, `bookshelf_create_author`, `bookshelf_delete_author`, `bookshelf_run_command`). Overrides for flagship/action endpoints live in the authoring script.

## Portmanteau registration — **do not go back to one tool per endpoint**
- `_GROUPS` buckets every `_TOOL_REGISTRY` name into one of 15 resource groups (`bookshelf_media_library`, `bookshelf_queue`, `bookshelf_config`, ...). `register_tools()` registers exactly one MCP tool per group via `_register_group`, which wraps the group's endpoint functions in a single `dispatch(operation, arguments)` closure. The endpoint functions themselves are unchanged — they're plain callables looked up by name, not separately-registered tools.
- `operation` is typed `Literal[<the group's endpoint names>]`, so FastMCP/pydantic validates it against the real endpoint list before `dispatch` ever runs — an invalid operation never reaches the group tool's body.
- Adding a new endpoint: add its entry to `_TOOL_REGISTRY` as before, then add its name to exactly one group in `_GROUPS`. `tests/test_tools.py::test_all_registry_names_grouped` fails if you forget.
- New resource area big enough to need its own group (rare): add a new `_GROUPS` key. Keep the total group count at or under ~15 — that ceiling is the entire point of this pattern.
- If you're tempted to add a per-endpoint `@mcp.tool` or an extra `mcp.add_tool` call outside `_register_group`, don't — every endpoint must be reachable only via its group's `operation` enum. A 221-tool server (one per endpoint) previously cost ~55k tokens of system-prompt budget on every session start; the 15-tool grouped version costs roughly a tenth of that.

## Annotations convention
- A group tool is `readOnlyHint=True` (`READONLY`) only when *every* operation in it is a GET (e.g. `bookshelf_wanted`, `bookshelf_calendar`). Mixed groups carry no hints.
- Per-operation write/destructive notes survive in the group tool's description: each operation line still ends with its original one-line doc, and destructive/write endpoints keep a `WRITE:`/`DESTRUCTIVE:` note in that doc string (see `_TOOL_REGISTRY`'s `doc` field).
- `READONLY`/`WRITE`/`DESTRUCTIVE` constants are kept for reference and for any future per-operation annotation work, but only `READONLY` is actually applied today (to all-GET groups).

## Auth and base path
- Auth: `X-Api-Key` header (generate in Bookshelf Settings > General > Security). Not bearer.
- `build_client` points at the origin with no path suffix; every registered tool carries its full path (`/api/v1/...` or `/ping`). `_req` raises `ToolError` with the API status and message on `>=400`.

## Release workflow
Always use the `make bump-*` targets to bump the version (`uv version --bump patch|minor|major`), which updates `pyproject.toml` and `uv.lock` together. Do NOT edit the version by hand.

- Bump: `make bump-patch` (or `bump-minor` / `bump-major`)
- Commit message is **just the version**, e.g. `0.1.2` — nothing else.
- Tag it `v<version>` (e.g. `v0.1.2`).
- Push main and the tag:
  ```
  git push origin main
  git push origin v<version>
  ```
- Deploy to the Proxmox host (root SSH key): pull the repo then reinstall the uv tool:
  ```
  ssh root@192.168.50.3 -- 'cd /root/bookshelf-mcp && git fetch origin && git reset --hard origin/main'
  ssh root@192.168.50.3 -- 'cd /root/bookshelf-mcp && uv tool install --force .'
  ```
  The host runs it via `uv tool install` → `/root/.local/bin/bookshelf-mcp` (not from the repo).

## Initial state
Version starts at `0.0.0` in the initial commit. No tag on the scaffold commit; releases begin at the first `make bump-*`.
