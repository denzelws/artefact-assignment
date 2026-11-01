"""``get_store_info`` tool: thin wrapper over the store identity block."""

import sqlite3

from pydantic import BaseModel

from emporio.data.store import StoreInfo, get_store_info
from emporio.llm.base import ToolDefinition


class GetStoreInfoArgs(BaseModel):
    """No arguments: the store has a single address and channel set."""


DEFINITION = ToolDefinition(
    name="get_store_info",
    description="Store address, hours, phones and email. Use before quoting contact info.",
    parameters=GetStoreInfoArgs.model_json_schema(),
)


def run(connection: sqlite3.Connection, args: GetStoreInfoArgs) -> StoreInfo:  # noqa: ARG001
    """Return the identity block (connection unused: info lives in code)."""
    return get_store_info()
