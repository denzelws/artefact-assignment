"""Typed store tools exposed to the agent.

One module per tool (Pydantic args in, Pydantic result out). The agent loop only
touches :func:`get_tool_definitions` (to declare tools to the model) and
:func:`execute_tool` (to run a model-requested call). Validation problems return
a JSON error payload so the model can self-correct instead of crashing the turn.
"""

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from emporio.llm.base import ToolDefinition

from . import (
    get_order_status,
    get_product,
    get_promotions,
    get_store_info,
    search_policies,
    search_products,
)


@dataclass(frozen=True)
class ToolEntry:
    """Wiring for one tool: schema, args model and runner."""

    definition: ToolDefinition
    args_model: type[BaseModel]
    run: Callable[[sqlite3.Connection, Any], BaseModel | list[BaseModel]]


TOOLS: dict[str, ToolEntry] = {
    "search_products": ToolEntry(search_products.DEFINITION, search_products.SearchProductsArgs, search_products.run),
    "get_product": ToolEntry(get_product.DEFINITION, get_product.GetProductArgs, get_product.run),
    "get_order_status": ToolEntry(
        get_order_status.DEFINITION, get_order_status.GetOrderStatusArgs, get_order_status.run
    ),
    "get_promotions": ToolEntry(
        get_promotions.DEFINITION, get_promotions.GetPromotionsArgs, get_promotions.run
    ),
    "search_policies": ToolEntry(
        search_policies.DEFINITION, search_policies.SearchPoliciesArgs, search_policies.run
    ),
    "get_store_info": ToolEntry(
        get_store_info.DEFINITION, get_store_info.GetStoreInfoArgs, get_store_info.run
    ),
}


def get_tool_definitions() -> list[ToolDefinition]:
    """Return the six tool declarations handed to the model."""
    return [entry.definition for entry in TOOLS.values()]


def execute_tool(name: str, connection: sqlite3.Connection, arguments: dict[str, Any]) -> str:
    """Validate ``arguments``, run the tool and return its JSON result for the model."""
    entry = TOOLS.get(name)
    if entry is None:
        return json.dumps({"ok": False, "error": f"Unknown tool: {name}."}, ensure_ascii=False)
    try:
        args = entry.args_model.model_validate(arguments)
    except ValidationError as exc:
        return json.dumps({"ok": False, "error": f"Invalid arguments: {exc.errors()}"}, ensure_ascii=False)
    result = entry.run(connection, args)
    if isinstance(result, list):
        return json.dumps(
            {"ok": True, "result": [item.model_dump() for item in result]}, ensure_ascii=False
        )
    return json.dumps({"ok": True, "result": result.model_dump()}, ensure_ascii=False)


__all__ = ["TOOLS", "ToolEntry", "execute_tool", "get_tool_definitions"]
