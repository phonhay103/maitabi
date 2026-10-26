"""MCP tool generation from core Input models (flat public wire schema).

fastmcp nests a single BaseModel parameter under an `"input"` key, which
would break the established flat schema, so each tool gets a real generated
keyword-only signature whose defaults are the model's `FieldInfo` objects —
byte-identical schema (types, constraints, defaults, descriptions) with the
descriptions living only in `core/inputs.py`.

Results are returned as a `ToolResult`: the text block is the exact JSON the
CLI prints (one `json.dumps` per edge, same settings), `structuredContent`
carries the same object parsed, and `isError` reflects the shared error
payload so a client does not report an upstream failure as a successful call.
"""

import json
from collections.abc import Callable
from typing import Any, cast

from fastmcp import FastMCP
from fastmcp.tools import Tool, ToolResult
from mcp.types import TextContent, ToolAnnotations

from maitabi.core.errors import is_error_payload
from maitabi.registry import ACTIONS, Action

# Every tool reads two public, read-only HTTP APIs: no state is mutated, the
# same arguments always answer the same question, and the data is external.
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# The payloads are upstream-shaped dicts (envelope, detail object, calendar
# matrix), so the honest schema is "an object"; the frozen fixture pins this.
OUTPUT_SCHEMA: dict[str, Any] = {"type": "object", "additionalProperties": True}


def _dumps(data: dict[str, Any]) -> str:
    """Serialize a service dict to the public JSON wire format."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def _result(data: dict[str, Any]) -> ToolResult:
    """Wrap a service dict as text + structured content, error state included."""
    return ToolResult(
        content=[TextContent(type="text", text=_dumps(data))],
        structured_content=data,
        is_error=is_error_payload(data),
    )


def make_tool_fn(action: Action) -> Callable[..., Any]:
    """Build the async tool function for one registry action.

    The body is mechanical: `service(InputModel(**kwargs))` → `ToolResult`.
    Tool name comes from `fn.__name__`, description from `fn.__doc__`.
    """
    fields = action.input_model.model_fields
    arglist = ", ".join(f"{name}=None" for name in fields)
    call = ", ".join(f"{name}={name}" for name in fields)
    source = (
        f"async def {action.tool}(*, {arglist}) -> _tool_result:\n"
        f"    return _tool_result(await _service(_model({call})))\n"
    )
    namespace = {
        "_tool_result": _result,
        "_model": action.input_model,
        "_service": action.service,
    }
    exec(source, namespace)  # noqa: S102 - identifiers come from model field names
    fn = namespace[action.tool]
    for name, info in fields.items():
        fn.__annotations__[name] = info.annotation
    # FieldInfo as kw-default: fastmcp/pydantic read constraints + requiredness
    # from it, exactly like an Annotated signature.
    cast(Any, fn).__kwdefaults__ = dict(fields.items())
    fn.__doc__ = action.doc
    return fn


def make_tool(action: Action) -> Tool:
    """Build the registered `Tool` for one registry action."""
    return Tool.from_function(
        make_tool_fn(action),
        name=action.tool,
        title=action.title,
        description=action.doc,
        annotations=READ_ONLY,
        tags={action.domain},
        output_schema=OUTPUT_SCHEMA,
    )


def register_tools(mcp: FastMCP) -> None:
    """Register every registry action as an MCP tool."""
    for action in ACTIONS:
        mcp.add_tool(make_tool(action))
