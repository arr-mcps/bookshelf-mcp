"""Offline tests: one per Bookshelf v1 endpoint, plus error-path tests.

No network. The list of operations is generated from the vendored spec at
tests/data/bookshelf_openapi.json (same skip rules as the authoring script),
and each tool call is checked against the exact HTTP request it should produce
(method, path incl. path-param substitution, query params) via
httpx.MockTransport, using FastMCP's in-memory Client (see
https://gofastmcp.com/development/tests).
"""

import json
import os

import httpx
import pytest
import pytest_asyncio
from fastmcp import Client
from fastmcp.exceptions import ToolError

import bookshelf_mcp

SPEC_PATH = os.path.join(os.path.dirname(__file__), "data", "bookshelf_openapi.json")

EXCLUDE_PATHS = {"/", "/{path}", "/content/{path}", "/api", "/login", "/logout",
                 "/feed/v1/calendar/readarr.ics"}
EXCLUDE_CONTENT_ENDPOINTS = {
    "/api/v1/mediacover/author/{authorId}/{filename}",
    "/api/v1/mediacover/book/{bookId}/{filename}",
    "/api/v1/log/file/{filename}",
    "/api/v1/log/file/update/{filename}",
}


def spec_ops():
    """(method, path, op) for every endpoint the server is expected to wrap."""
    d = json.load(open(SPEC_PATH))
    ops = []
    for p, methods in d["paths"].items():
        for m, op in methods.items():
            if m in ("head", "parameters"):
                continue
            if p in EXCLUDE_PATHS or p in EXCLUDE_CONTENT_ENDPOINTS:
                continue
            if not (p.startswith("/api/v1") or p == "/ping"):
                continue
            ops.append((m.upper(), p, op))
    return ops


def registry_for(method, path):
    for spec in bookshelf_mcp._TOOL_REGISTRY:
        if spec["method"] == method and spec["path"] == path:
            return spec
    raise AssertionError(f"no registry entry for {method} {path}")


def op_to_args(spec):
    """Build call args for a tool from its registry entry: path params get a
    sentinel value per their declared type."""
    args = {}
    for p in spec["pp"]:
        args[p["name"]] = "abc" if p["type"] == "str" else 1
    return args


def expected_path(spec):
    path = spec["path"]
    for p in spec["pp"]:
        path = path.replace("{" + p["wire"] + "}", "abc" if p["type"] == "str" else "1")
    return path


class Recorder:
    """Captures the single request made during a test and replays a canned response."""

    def __init__(self):
        self.method = None
        self.url = None
        self.headers = None
        self.params = None
        self.json = None
        self.response = httpx.Response(200, json={"success": True})

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.method = request.method
        self.url = request.url
        self.headers = request.headers
        self.params = request.url.params
        self.json = json.loads(request.content) if request.content else None
        return self.response


@pytest.fixture
def recorder():
    return Recorder()


@pytest_asyncio.fixture
async def server(recorder, monkeypatch):
    transport = httpx.MockTransport(recorder.handler)
    client = bookshelf_mcp.build_client("http://bookshelf.example.com:8787", "test-key", transport=transport)
    monkeypatch.setattr(bookshelf_mcp, "_client", client)
    yield bookshelf_mcp.mcp
    await client.aclose()


async def call(server, tool, **kwargs):
    async with Client(server) as c:
        return await c.call_tool(tool, kwargs)


# --- one test per endpoint ---------------------------------------------------

@pytest.mark.parametrize(
    "method,path",
    [(m, p) for m, p, _ in spec_ops()],
    ids=[f"{m.lower()}_{p}" for m, p, _ in spec_ops()],
)
async def test_endpoint_mapping(server, recorder, method, path):
    spec = registry_for(method, path)
    await call(server, spec["name"], **op_to_args(spec))
    assert recorder.method == method
    assert recorder.url.path == expected_path(spec)


# --- coverage: registry == spec ---------------------------------------------

def test_registry_covers_spec_exactly():
    spec_ops_set = {(m, p) for m, p, _ in spec_ops()}
    registry_ops = {(s["method"], s["path"]) for s in bookshelf_mcp._TOOL_REGISTRY}
    assert registry_ops == spec_ops_set


def test_all_registered_tools_have_unique_names():
    names = [s["name"] for s in bookshelf_mcp._TOOL_REGISTRY]
    assert len(names) == len(set(names))


# --- query params --------------------------------------------------------------

async def test_query_params_use_wire_names(server, recorder):
    await call(server, "bookshelf_list_history", page=2, page_size=50, sort_key="date", sort_direction="descending")
    assert recorder.params["page"] == "2"
    assert recorder.params["pageSize"] == "50"
    assert recorder.params["sortKey"] == "date"
    assert recorder.params["sortDirection"] == "descending"


async def test_list_params_serialize_repeatedly(server, recorder):
    await call(server, "bookshelf_list_book", book_ids=[1, 2, 3])
    assert recorder.params.get_list("bookIds") == ["1", "2", "3"]


async def test_empty_optional_params_are_omitted(server, recorder):
    await call(server, "bookshelf_list_book")
    assert "authorId" not in recorder.params
    assert "titleSlug" not in recorder.params


async def test_lookup_and_path_id_encoding(server, recorder):
    await call(server, "bookshelf_lookup_author", term="Brandon Sanderson")
    assert recorder.url.path == "/api/v1/author/lookup"
    assert recorder.params["term"] == "Brandon Sanderson"

    await call(server, "bookshelf_get_author", id=42)
    assert recorder.url.path == "/api/v1/author/42"


# --- request bodies ------------------------------------------------------------

async def test_body_sent_as_json(server, recorder):
    body = {"foreignAuthorId": "12345", "qualityProfileId": 1, "metadataProfileId": 1, "rootFolderPath": "/books"}
    await call(server, "bookshelf_create_author", body=body)
    assert recorder.json == body


async def test_array_body_sent_as_json(server, recorder):
    body = [{"id": 1, "monitored": False}]
    await call(server, "bookshelf_commit_manual_import", body=body)
    assert recorder.json == body


async def test_get_requests_have_no_body(server, recorder):
    await call(server, "bookshelf_list_author")
    assert recorder.json is None


# --- auth header ---------------------------------------------------------------

async def test_api_key_sent_as_x_api_key_header(server, recorder):
    await call(server, "bookshelf_list_tag")
    assert recorder.headers["x-api-key"] == "test-key"


async def test_no_api_key_means_no_auth_header(recorder, monkeypatch):
    transport = httpx.MockTransport(recorder.handler)
    client = bookshelf_mcp.build_client("http://bookshelf.example.com:8787", None, transport=transport)
    monkeypatch.setattr(bookshelf_mcp, "_client", client)
    await call(bookshelf_mcp.mcp, "bookshelf_list_tag")
    assert "x-api-key" not in recorder.headers
    await client.aclose()


# --- ping outside /api/v1 --------------------------------------------------------

async def test_ping_hits_unversioned_path(server, recorder):
    await call(server, "bookshelf_ping")
    assert recorder.method == "GET"
    assert recorder.url.path == "/ping"


# --- error paths -----------------------------------------------------------------

async def test_404_error_message_reaches_caller(server, recorder):
    recorder.response = httpx.Response(404, json={"message": "Author not found"})
    with pytest.raises(ToolError, match="Author not found"):
        await call(server, "bookshelf_get_author", id=999999)


async def test_401_error_surfaces_status(server, recorder):
    recorder.response = httpx.Response(401, json={"message": "Unauthorized"})
    with pytest.raises(ToolError, match="401"):
        await call(server, "bookshelf_list_tag")


async def test_400_error_surfaces_status(server, recorder):
    recorder.response = httpx.Response(400, json={"message": "Invalid request"})
    with pytest.raises(ToolError, match="400"):
        await call(server, "bookshelf_create_author", body={})


async def test_non_json_error_body_does_not_crash(server, recorder):
    recorder.response = httpx.Response(502, text="<html>Bad Gateway</html>")
    with pytest.raises(ToolError, match="502"):
        await call(server, "bookshelf_list_tag")


# --- main() ------------------------------------------------------------------

def test_main_requires_bookshelf_url(monkeypatch):
    monkeypatch.delenv("BOOKSHELF_URL", raising=False)
    with pytest.raises(SystemExit):
        bookshelf_mcp.main()
