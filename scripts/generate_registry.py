#!/usr/bin/env python3
"""Generate the `_TOOL_REGISTRY` literal for bookshelf_mcp.py from the vendored
Bookshelf (Readarr fork) OpenAPI spec at tests/data/bookshelf_openapi.json.

Usage:
    uv run python scripts/generate_registry.py            # print to stdout
    uv run python scripts/generate_registry.py -o tmp     # print to tmp

The registry lists one entry per JSON-producing endpoint under `/api/v1` plus
`GET /ping`. Binary/text endpoints (media covers, raw log file contents), the
`.ics` calendar feed, static web routes, `/login`/`/logout`, and `/api`
(swagger metadata) are skipped - `_req` JSON-decodes every response.

Tool naming is `bookshelf_<verb>_<resource>` derived from method + path, with a
curated override map for flagship/action endpoints, config GETs, and provider
test/schema/action/bulk endpoints. If two endpoints would collide, the script
fails loudly - add an override.
"""

from __future__ import annotations

import json
import re
import sys

SPEC_PATH = "tests/data/bookshelf_openapi.json"

EXCLUDED_PATHS = {"/", "/{path}", "/content/{path}", "/api", "/login", "/logout",
                  "/feed/v1/calendar/readarr.ics"}
EXCLUDED_CONTENT_ENDPOINTS = {
    "/api/v1/mediacover/author/{authorId}/{filename}",
    "/api/v1/mediacover/book/{bookId}/{filename}",
    "/api/v1/log/file/{filename}",
    "/api/v1/log/file/update/{filename}",
}

# (method, path) -> explicit tool name. Flagship/action endpoints and any name
# collisions the generic derivation would produce.
NAME_OVERRIDES = {
    ("POST", "/api/v1/command"): "bookshelf_run_command",
    ("GET", "/api/v1/search"): "bookshelf_search",
    ("POST", "/api/v1/release"): "bookshelf_search_releases",
    ("POST", "/api/v1/release/push"): "bookshelf_push_release",
    ("POST", "/api/v1/manualimport"): "bookshelf_commit_manual_import",
    ("POST", "/api/v1/history/failed/{id}"): "bookshelf_mark_history_failed",
    ("POST", "/api/v1/bookshelf"): "bookshelf_add_books_to_shelf",
    ("PUT", "/api/v1/book/monitor"): "bookshelf_update_books_monitored",
    ("PUT", "/api/v1/qualitydefinition/update"): "bookshelf_update_quality_definitions",
    ("PUT", "/api/v1/delayprofile/reorder/{id}"): "bookshelf_reorder_delayprofile",
    ("GET", "/api/v1/author/lookup"): "bookshelf_lookup_author",
    ("GET", "/api/v1/book/lookup"): "bookshelf_lookup_book",
    ("GET", "/api/v1/parse"): "bookshelf_get_parse",
    ("GET", "/api/v1/rename"): "bookshelf_get_rename",
    ("GET", "/api/v1/retag"): "bookshelf_get_retag",
    ("GET", "/api/v1/diskspace"): "bookshelf_get_diskspace",
    ("GET", "/api/v1/health"): "bookshelf_get_health",
    ("GET", "/api/v1/indexerflag"): "bookshelf_get_indexerflag",
    ("GET", "/api/v1/localization"): "bookshelf_get_localization",
    ("GET", "/api/v1/queue/details"): "bookshelf_get_queue_details",
    ("GET", "/api/v1/queue/status"): "bookshelf_get_queue_status",
    ("POST", "/api/v1/queue/grab/bulk"): "bookshelf_grab_queue_bulk",
    ("POST", "/api/v1/queue/grab/{id}"): "bookshelf_grab_queue_item",
    ("PUT", "/api/v1/author/editor"): "bookshelf_bulk_update_author",
    ("DELETE", "/api/v1/author/editor"): "bookshelf_bulk_delete_author",
    ("PUT", "/api/v1/book/editor"): "bookshelf_bulk_update_book",
    ("DELETE", "/api/v1/book/editor"): "bookshelf_bulk_delete_book",
    ("PUT", "/api/v1/bookfile/editor"): "bookshelf_bulk_update_bookfile",
    ("DELETE", "/api/v1/bookfile/bulk"): "bookshelf_bulk_delete_bookfile",
    ("DELETE", "/api/v1/blocklist/bulk"): "bookshelf_bulk_delete_blocklist",
    ("DELETE", "/api/v1/queue/bulk"): "bookshelf_bulk_delete_queue",
    ("POST", "/api/v1/system/restart"): "bookshelf_restart",
    ("POST", "/api/v1/system/shutdown"): "bookshelf_shutdown",
    ("POST", "/api/v1/system/backup/restore/upload"): "bookshelf_restore_backup_upload",
    ("POST", "/api/v1/system/backup/restore/{id}"): "bookshelf_restore_backup",
    ("GET", "/api/v1/system/routes"): "bookshelf_get_system_routes",
    ("GET", "/api/v1/system/routes/duplicate"): "bookshelf_get_system_routes_duplicate",
    ("GET", "/api/v1/system/status"): "bookshelf_get_system_status",
    ("GET", "/api/v1/system/task"): "bookshelf_get_system_task",
    ("GET", "/api/v1/system/task/{id}"): "bookshelf_get_system_task_by_id",
    ("GET", "/ping"): "bookshelf_ping",
}

# Config GETs return a single resource (not a collection) - override list_->get_,
# and the {id} GETs to *_by_id so they don't collide with the plain GET.
for _cfg in ("development", "downloadclient", "host", "indexer", "mediamanagement",
             "metadataprovider", "naming", "ui"):
    NAME_OVERRIDES[("GET", f"/api/v1/config/{_cfg}")] = f"bookshelf_get_config_{_cfg}"
    NAME_OVERRIDES[("GET", f"/api/v1/config/{_cfg}/{{id}}")] = f"bookshelf_get_config_{_cfg}_by_id"
NAME_OVERRIDES[("GET", "/api/v1/config/naming/examples")] = "bookshelf_get_config_naming_examples"

# Provider resources with test/schema/action/bulk endpoints.
for _res in ("downloadclient", "indexer", "importlist", "notification", "metadata"):
    NAME_OVERRIDES[("POST", f"/api/v1/{_res}/action/{{name}}")] = f"bookshelf_action_{_res}"
    NAME_OVERRIDES[("PUT", f"/api/v1/{_res}/bulk")] = f"bookshelf_bulk_update_{_res}"
    NAME_OVERRIDES[("DELETE", f"/api/v1/{_res}/bulk")] = f"bookshelf_bulk_delete_{_res}"
    NAME_OVERRIDES[("GET", f"/api/v1/{_res}/schema")] = f"bookshelf_get_{_res}_schema"
    NAME_OVERRIDES[("POST", f"/api/v1/{_res}/test")] = f"bookshelf_test_{_res}"
    NAME_OVERRIDES[("POST", f"/api/v1/{_res}/testall")] = f"bookshelf_test_all_{_res}"

NAME_OVERRIDES[("GET", "/api/v1/customformat/schema")] = "bookshelf_get_customformat_schema"
NAME_OVERRIDES[("GET", "/api/v1/metadataprofile/schema")] = "bookshelf_get_metadataprofile_schema"
NAME_OVERRIDES[("GET", "/api/v1/qualityprofile/schema")] = "bookshelf_get_qualityprofile_schema"

METHOD_VERB_SINGLE = {"GET": "get", "POST": "create", "PUT": "update", "DELETE": "delete"}

TYPE_MAP = {"number": "int", "integer": "int", "boolean": "bool", "string": "str", "array": "list[Any]"}


def _resource_from_path(path: str) -> str:
    segments = [s for s in path.split("/") if s]
    segments = [s for s in segments if not re.fullmatch(r"\{.*\}", s)]
    if segments[:2] == ["api", "v1"]:
        segments = segments[2:]
    resource = "_".join(segments)
    resource = re.sub(r"_+", "_", resource).strip("_").lower()
    return resource or "root"


def _verb(method: str, path: str, has_params: bool) -> str:
    if method == "GET":
        return "list" if not has_params else "get"
    return METHOD_VERB_SINGLE[method]


def _snake(name: str) -> str:
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    name = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return name.lower().strip("_")


def _derive_name(method: str, path: str) -> str:
    explicit = NAME_OVERRIDES.get((method, path))
    if explicit:
        return explicit
    has_params = "{" in path
    verb = _verb(method, path, has_params)
    resource = _resource_from_path(path)
    return f"bookshelf_{verb}_{resource}"


def _params(kind: str, op: dict, taken: set[str]) -> list[dict]:
    out = []
    for prm in op.get("parameters", []) or []:
        if prm.get("in") != kind:
            continue
        schema = prm.get("schema", {}) or {}
        ptype = TYPE_MAP.get(schema.get("type"), "str")
        default = schema.get("default")
        name = _snake(prm["name"])
        if name in taken:
            name = f"{name}_q"
        taken.add(name)
        out.append(
            {
                "name": name,
                "wire": prm["name"],
                "type": ptype,
                "required": bool(prm.get("required")) and kind == "query",
                "default": None if default is None else default,
            }
        )
    return out


def _body_kind(op: dict) -> str:
    rb = op.get("requestBody")
    if not rb:
        return "none"
    schema = rb.get("content", {}).get("application/json", {}).get("schema", {}) or {}
    if schema.get("type") == "array":
        return "list"
    return "dict"


# (method, path) -> hand-written tool docstring. Flagship/action endpoints the
# generic template would describe too generically.
DOC_OVERRIDES = {
    ("POST", "/api/v1/command"): "Run a Bookshelf command (body is a CommandResource with a `name`, e.g. RefreshAuthor, AuthorSearch, BookSearch, DownloadedBooksScan, RenamedBookFiles, RescanFolders, MetadataRefresh). WRITE: this modifies your Bookshelf instance.",
    ("GET", "/api/v1/search"): "Search for new books/authors on the metadata provider by term and return the matches to add.",
    ("POST", "/api/v1/release"): "Trigger a release search for a book and grab the given release. WRITE: this modifies your Bookshelf instance.",
    ("POST", "/api/v1/release/push"): "Push a release to Bookshelf (e.g. from an external downloader); body is a ReleaseResource with title and downloadUrl.",
    ("POST", "/api/v1/manualimport"): "Commit manual imports for the given files. Body is a list of ManualImportUpdateResource. WRITE: this modifies your Bookshelf instance.",
    ("POST", "/api/v1/history/failed/{id}"): "Mark a history event as failed and trigger a re-search. WRITE: this modifies your Bookshelf instance.",
    ("POST", "/api/v1/bookshelf"): "Add the given books to a Goodreads/Hardcover shelf. Body is a BookshelfResource with bookshelfId and bookIds.",
    ("PUT", "/api/v1/book/monitor"): "Set the monitored state of books in bulk. Body is a BooksMonitoredResource with bookIds and monitored.",
    ("GET", "/api/v1/author/lookup"): "Search the metadata provider for authors by term.",
    ("GET", "/api/v1/book/lookup"): "Search the metadata provider for books by term.",
    ("GET", "/api/v1/parse"): "Parse a file or release title and show how Bookshelf interprets it.",
    ("GET", "/api/v1/rename"): "List proposed renames for an author or book (files that would be renamed on the next rename task).",
    ("GET", "/api/v1/retag"): "List proposed file retags for an author or book.",
    ("POST", "/api/v1/queue/grab/bulk"): "Grab multiple queue items now. Body is a QueueBulkResource with ids.",
    ("POST", "/api/v1/queue/grab/{id}"): "Grab a single queue item now.",
    ("GET", "/api/v1/queue/details"): "List detailed queue items for an author or books.",
    ("GET", "/api/v1/queue/status"): "Get queue statistics: total/full count and warnings.",
    ("GET", "/api/v1/system/status"): "Get system status: app name, version, OS, build, and runtime.",
    ("POST", "/api/v1/system/restart"): "Restart the Bookshelf service.",
    ("POST", "/api/v1/system/shutdown"): "Shut down the Bookshelf service.",
}


def _human(resource: str) -> str:
    """book_overview -> 'book overview' (kept lowercase, used mid-sentence)."""
    return resource.replace("_", " ")


def _doc(op: dict, method: str, path: str, qp: list[dict]) -> str:
    explicit = DOC_OVERRIDES.get((method, path))
    if explicit:
        return explicit
    has_params = "{" in path
    is_bulk = "/bulk" in path or "/editor" in path
    resource = _human(_resource_from_path(path))
    qparams = ", ".join(q["wire"] for q in qp)
    if method == "GET" and not has_params:
        if is_bulk:
            body = "Bulk"
        else:
            body = "List"
        doc = f"{body} {resource}."
    elif method == "GET" and has_params:
        doc = f"Fetch a single {resource} by id."
    elif method == "POST":
        doc = f"Create {resource}."
    elif method == "PUT":
        if is_bulk:
            doc = f"Bulk update {resource}."
        else:
            doc = f"Update {resource}."
    else:  # DELETE
        if is_bulk:
            doc = f"Bulk delete {resource}."
        else:
            doc = f"Delete {resource}."
    if qparams:
        doc += f" Query params: {qparams}."
    if method in ("POST", "PUT"):
        doc += " WRITE: this modifies your Bookshelf instance."
    if method == "DELETE":
        doc += " DESTRUCTIVE: this deletes data."
    return doc


def _quote(v):
    if isinstance(v, bool):
        return "True" if v else "False"
    return repr(v)


def build_entries() -> list[dict]:
    d = json.load(open(SPEC_PATH))
    entries = []
    seen_names: dict[str, str] = {}
    for path, methods in d["paths"].items():
        if path in EXCLUDED_PATHS or path in EXCLUDED_CONTENT_ENDPOINTS:
            continue
        for method, op in methods.items():
            if method in ("head", "options", "parameters"):
                continue
            if not (path.startswith("/api/v1") or path == "/ping"):
                continue
            name = _derive_name(method.upper(), path)
            if name in seen_names:
                raise SystemExit(f"collision: {name} for {method.upper()} {path} and {seen_names[name]}")
            seen_names[name] = f"{method.upper()} {path}"
            taken: set[str] = set()
            pp = _params("path", op, taken)
            qp = _params("query", op, taken)
            entry = {
                "name": name,
                "method": method.upper(),
                "path": path,
                "pp": pp,
                "qp": qp,
                "bk": _body_kind(op),
                "doc": _doc(op, method.upper(), path, qp),
            }
            entries.append(entry)
    return entries


def render(entries: list[dict]) -> str:
    lines = ["_TOOL_REGISTRY: list[dict[str, Any]] = ["]
    for e in entries:
        lines.append(" {'name': %s," % _quote(e["name"]))
        lines.append("  'method': %s," % _quote(e["method"]))
        lines.append("  'path': %s," % _quote(e["path"]))
        if e["pp"]:
            lines.append("  'pp': [")
            for p in e["pp"]:
                lines.append("          {'name': %s, 'wire': %s, 'type': %s}," % (_quote(p["name"]), _quote(p["wire"]), _quote(p["type"])))
            lines.append("         ],")
        else:
            lines.append("  'pp': [],")
        if e["qp"]:
            lines.append("  'qp': [")
            for q in e["qp"]:
                req = ", 'required': True" if q["required"] else ""
                lines.append(
                    "          {'name': %s, 'wire': %s, 'type': %s, 'default': %s%s},"
                    % (_quote(q["name"]), _quote(q["wire"]), _quote(q["type"]), _quote(q["default"]), req)
                )
            lines.append("         ],")
        else:
            lines.append("  'qp': [],")
        lines.append("  'bk': %s," % _quote(e["bk"]))
        lines.append("  'doc': %s," % _quote(e["doc"]))
        lines.append(" },")
    lines.append("]")
    return "\n".join(lines)


def main() -> None:
    entries = build_entries()
    text = render(entries)
    if "-o" in sys.argv:
        out = sys.argv[sys.argv.index("-o") + 1]
        with open(out, "w") as f:
            f.write(text + "\n")
    else:
        print(text)
    print(f"\n# {len(entries)} tools generated from {SPEC_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
