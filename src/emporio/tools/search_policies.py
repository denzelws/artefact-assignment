"""``search_policies`` tool: thin wrapper over the ranked policy search."""

import sqlite3

from pydantic import BaseModel, Field

from emporio.data.policies import search_policies
from emporio.llm.base import ToolDefinition


class SearchPoliciesArgs(BaseModel):
    """Typed arguments the model provides for a policy lookup."""

    query: str = Field(description="Customer question in Portuguese, e.g. 'prazo de troca'.")
    limit: int = Field(default=3, ge=1, le=10, description="Max sections to return.")


class PolicyHit(BaseModel):
    """One matching manual section."""

    id: str
    title: str
    text: str


DEFINITION = ToolDefinition(
    name="search_policies",
    description="Store policies (returns, shipping, payments, warranty, hours). Falls back to index.",
    parameters=SearchPoliciesArgs.model_json_schema(),
)


def run(connection: sqlite3.Connection, args: SearchPoliciesArgs) -> list[PolicyHit]:  # noqa: ARG001
    """Rank sections (connection unused: policies live in code, not SQLite)."""
    return [
        PolicyHit(id=section.id, title=section.title, text=section.text)
        for section in search_policies(args.query, args.limit)
    ]
