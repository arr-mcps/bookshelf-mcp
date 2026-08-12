# bookshelf_openapi.json

Bookshelf v1 OpenAPI spec, vendored from the Bookshelf repo so the tool
registry and tests stay reproducible and work offline.

- Source: `src/Readarr.Api.V1/openapi.json`
- Branch: `develop`
- The `_TOOL_REGISTRY` in `bookshelf_mcp.py` is generated from this file by
  `scripts/generate_registry.py`. To refresh: download a newer `openapi.json`,
  regenerate the registry, and re-run the tests.
