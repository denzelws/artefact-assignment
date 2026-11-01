"""``search_products`` tool: find instruments by text, category, price, availability."""

import sqlite3

from pydantic import BaseModel, Field

from emporio.llm.base import ToolDefinition

from ._pricing import price_block
from ._text import normalize, query_tokens, stem


class SearchProductsArgs(BaseModel):
    """Typed arguments the model provides for a product search."""

    query: str = Field(default="", description="Free-text match against name and description.")
    category: str = Field(
        default="", description="Category id or name (e.g. '5', 'violoes', 'ukuleles')."
    )
    max_price: float | None = Field(default=None, description="Upper price bound in BRL.")
    in_stock_only: bool = Field(default=False, description="Only available items (active + stock).")
    limit: int = Field(default=10, ge=1, le=50, description="Max results, cheapest first.")


class ProductSummary(BaseModel):
    """One matching product with resolved promotional/PIX pricing."""

    product_id: int
    name: str
    price_brl: float
    category: str
    status: str
    stock_quantity: int
    promo_price: float | None = None
    pix_eligible: bool = True
    pix_price: float | None = None


DEFINITION = ToolDefinition(
    name="search_products",
    description="Search instruments by text, category, max price and availability. Cheapest first.",
    parameters=SearchProductsArgs.model_json_schema(),
)


def _resolve_category(connection: sqlite3.Connection, category: str) -> int | None:
    """Match a category id or accent-insensitive name; None when blank."""
    wanted = normalize(category)
    if not wanted:
        return None
    if wanted.isdigit():
        row = connection.execute(
            "SELECT category_id FROM categories WHERE category_id = ?", (int(wanted),)
        ).fetchone()
        return int(row[0]) if row else -1
    for category_id, name in connection.execute("SELECT category_id, name FROM categories"):
        if stem(normalize(str(name))) == stem(wanted):
            return int(category_id)
    return -1


def run(connection: sqlite3.Connection, args: SearchProductsArgs) -> list[ProductSummary]:
    """Run the search; unknown categories yield an empty list, never an error."""
    category_id = _resolve_category(connection, args.category)
    if category_id == -1:
        return []

    clauses = ["p.category_id = c.category_id"]
    params: list[object] = []
    if category_id is not None:
        clauses.append("p.category_id = ?")
        params.append(category_id)
    if args.max_price is not None:
        clauses.append("p.price_brl <= ?")
        params.append(args.max_price)
    if args.in_stock_only:
        clauses.append("p.status = 'active' AND p.stock_quantity > 0")

    rows = connection.execute(
        "SELECT p.product_id, p.name, p.price_brl, c.name, p.status, p.stock_quantity, p.description "
        "FROM products p, categories c "
        f"WHERE {' AND '.join(clauses)} ORDER BY p.price_brl ASC, p.product_id ASC",
        params,
    ).fetchall()

    tokens = query_tokens(args.query)
    summaries: list[ProductSummary] = []
    for product_id, name, price, category_name, status, stock, description in rows:
        if tokens:
            haystack = normalize(f"{name} {description or ''}")
            if not all(token in haystack for token in tokens):
                continue
        summaries.append(
            ProductSummary(
                product_id=int(product_id),
                name=str(name),
                price_brl=float(price),
                category=str(category_name),
                status=str(status),
                stock_quantity=int(stock),
                **price_block(connection, int(product_id), float(price)),  # type: ignore[arg-type]
            )
        )
        if len(summaries) >= args.limit:
            break
    return summaries
