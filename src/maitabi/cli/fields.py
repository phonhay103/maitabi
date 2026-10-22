"""Field-level CLI plan derived from Pydantic `FieldInfo` (presentation + coercion).

Both `parser.py` (argparse flags) and `commands.py` (namespace → Input model)
go through `plan_field`, so a field's flag type and its coercion can never
drift apart. Must NOT import fastmcp/mcp/server/mcp.
"""

import types
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import Union, get_args, get_origin

from pydantic.fields import FieldInfo

# Presentation-only metavars for string-ish flags (argparse's default is the
# uppercased dest, which is noisy for CSV/range inputs).
_METAVARS = {"day": "DAY", "course_no": "NO", "year_month": "YYYY-MM"}


@dataclass(frozen=True)
class FieldPlan:
    """How one model field is exposed on the CLI."""

    flag: str  # e.g. "--course-cd"
    metavar: str | None
    required: bool
    default: object
    arg_type: type | None  # None when store_true
    store_true: bool
    choices: list[object] | None
    coerce: Callable[[str], object] | None  # applied to string input, if any


def annotation_members(annotation: object) -> list[object]:
    """Flatten a (possibly Optional/union) annotation into its members."""
    if get_origin(annotation) in (Union, types.UnionType):
        return list(get_args(annotation))
    return [annotation]


def _parse_course_nos(raw: str) -> int | list[int]:
    """CSV → int when single (single-vs-batch changes the response shape)."""
    nums = [int(p.strip()) for p in raw.split(",") if p.strip()]
    return nums[0] if len(nums) == 1 else nums


def _parse_id_list(raw: str) -> list[int] | None:
    if not raw:
        return None
    return [int(p.strip()) for p in raw.split(",") if p.strip()]


def _enum_of(members: list[object]) -> type[IntEnum] | None:
    for member in members:
        if get_origin(member) is None and isinstance(member, type):
            try:
                if issubclass(member, IntEnum):
                    return member
            except TypeError:  # pragma: no cover - defensive
                continue
    return None


def plan_field(name: str, info: FieldInfo) -> FieldPlan:
    """Classify a model field into an argparse flag + string coercion.

    Rules (in precedence order):
    - bool              → --flag (store_true)
    - IntEnum (+Optional) → --flag int with enum choices (defaults kept)
    - plain int (+Optional) → --flag int (model's ge/le validate ranges)
    - anything else (str, CSV lists, day unions) → --flag str; unions
      containing str pass through raw (the model parses ranges), CSV list
      fields coerce to int/list here.
    """
    flag = "--" + name.replace("_", "-")
    metavar = "IDS" if name.startswith("category_nos") else _METAVARS.get(name)
    required = info.is_required()
    default = None if required else info.default
    members = [m for m in annotation_members(info.annotation) if m is not type(None)]

    if info.annotation is bool:
        return FieldPlan(flag, metavar, False, bool(default), None, True, None, None)

    enum_cls = _enum_of(members)
    if enum_cls is not None:
        if isinstance(default, IntEnum):
            default = int(default)
        return FieldPlan(
            flag,
            metavar,
            required,
            default,
            int,
            False,
            [member.value for member in enum_cls],
            None,
        )

    if all(m is int for m in members):
        return FieldPlan(flag, metavar, required, default, int, False, None, None)

    coerce: Callable[[str], object] | None = None
    if any(m == list[int] for m in members) and not any(m is str for m in members):
        # `int | list[int]` (course_no) keeps single-as-int; bare `list[int]`
        # (category_nos*) always yields a list.
        coerce = _parse_course_nos if any(m is int for m in members) else _parse_id_list
    return FieldPlan(flag, metavar, required, default, str, False, None, coerce)
