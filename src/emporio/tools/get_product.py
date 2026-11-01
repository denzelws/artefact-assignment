"""``get_product`` tool: full detail for one product by id."""

import sqlite3

from pydantic import BaseModel, Field

from emporio.llm.base import ToolDefinition

from ._pricing import price_block


class GetProductArgs(BaseModel):
    """Typed arguments the model provides for a product lookup."""

    product_id: int = Field(description="Product id, e.g. 95 for the Takamine GD20.")


class ProductDetail(BaseModel):
    """Full product record with resolved pricing, or a not-found marker."""

    found: bool
    product_id: int | None = None
    name: str | None = None
    price_brl: float | None = None
    category: str | None = None
    description: str | None = None
    status: str | None = None
    stock_quantity: int | None = None
    specs: str | None = None
    promo_price: float | None = None
    pix_eligible: bool = True
    pix_price: float | None = None
    message: str | None = None


DEFINITION = ToolDefinition(
    name="get_product",
    description="Full detail (price, stock, status, specs) for one product id.",
    parameters=GetProductArgs.model_json_schema(),
)


def run(connection: sqlite3.Connection, args: GetProductArgs) -> ProductDetail:
    """Fetch one product; unknown ids return found=False instead of raising."""
    row = connection.execute(
        "SELECT p.product_id, p.name, p.price_brl, c.name, p.description, "
        "p.status, p.stock_quantity, p.specs "
        "FROM products p, categories c "
        "WHERE p.category_id = c.category_id AND p.product_id = ?",
        (args.product_id,),
    ).fetchone()
    if row is None:
        return ProductDetail(found=False, message=f"Product {args.product_id} does not exist.")
    price = float(row[2])
    return ProductDetail(
        found=True,
        product_id=int(row[0]),
        name=str(row[1]),
        price_brl=price,
        category=str(row[3]),
        description=row[4],
        status=str(row[5]),
        stock_quantity=int(row[6]),
        specs=row[7],
        **price_block(connection, int(row[0]), price),  # type: ignore[arg-type]
    )
