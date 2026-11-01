"""``get_promotions`` tool: active promotions only, with final prices.

Every returned promo carries ``pix_eligible=False``: the 5% PIX never stacks on
promotional prices, so the model quotes the promo price as-is instead of computing.
"""

import sqlite3

from pydantic import BaseModel, Field

from emporio.llm.base import ToolDefinition


class GetPromotionsArgs(BaseModel):
    """Typed arguments the model provides for a promotion lookup."""

    product_id: int | None = Field(
        default=None, description="Restrict to one product id; omit for all active promos."
    )


class Promotion(BaseModel):
    """One active promotion with the final price already computed."""

    promotion_id: int
    product_id: int
    product_name: str
    discount_percent: float
    original_price_brl: float
    promo_price_brl: float
    pix_eligible: bool = False
    description: str | None = None


DEFINITION = ToolDefinition(
    name="get_promotions",
    description="Active promotions with final prices. PIX discount never stacks on these.",
    parameters=GetPromotionsArgs.model_json_schema(),
)


def run(connection: sqlite3.Connection, args: GetPromotionsArgs) -> list[Promotion]:
    """List active promos (all, or for one product); expired ones never appear."""
    query = (
        "SELECT pr.promotion_id, pr.product_id, p.name, pr.discount_percent, "
        "p.price_brl, pr.description FROM promotions pr, products p "
        "WHERE pr.product_id = p.product_id AND pr.is_active = 1"
    )
    params: list[object] = []
    if args.product_id is not None:
        query += " AND pr.product_id = ?"
        params.append(args.product_id)
    query += " ORDER BY pr.promotion_id ASC"
    return [
        Promotion(
            promotion_id=int(row[0]),
            product_id=int(row[1]),
            product_name=str(row[2]),
            discount_percent=float(row[3]),
            original_price_brl=float(row[4]),
            promo_price_brl=round(float(row[4]) * (1 - float(row[3]) / 100), 2),
            description=row[5],
        )
        for row in connection.execute(query, params).fetchall()
    ]
