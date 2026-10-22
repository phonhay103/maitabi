"""MCP tool generation from core Input models (flat public wire schema).

fastmcp nests a single BaseModel parameter under an `"input"` key, which
would break the established flat schema, so each tool gets a real generated
keyword-only signature whose defaults are the model's `FieldInfo` objects —
byte-identical schema (types, constraints, defaults, descriptions) with the
descriptions living only in `core/inputs.py`.
"""

import json
from collections.abc import Callable
from typing import Any, cast

from fastmcp import FastMCP

from maitabi_mcp_server.registry import ACTIONS, Action


def _dumps(data: dict[str, Any]) -> str:
    """Serialize a service dict to the public JSON wire format."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def make_tool_fn(action: Action) -> Callable[..., Any]:
    """Build the async tool function for one registry action.

    The body is mechanical: `service(InputModel(**kwargs))` → JSON string.
    Tool name comes from `fn.__name__`, description from `fn.__doc__`.
    """
    fields = action.input_model.model_fields
    arglist = ", ".join(f"{name}=None" for name in fields)
    call = ", ".join(f"{name}={name}" for name in fields)
    source = f"async def {action.tool}(*, {arglist}) -> str:\n    return _dumps(await _service(_model({call})))\n"
    namespace = {
        "_dumps": _dumps,
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


def register_tools(mcp: FastMCP) -> None:
    """Register every registry action as an MCP tool."""
    for action in ACTIONS:
        mcp.add_tool(make_tool_fn(action))
