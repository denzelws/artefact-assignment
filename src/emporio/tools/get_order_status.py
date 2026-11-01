"""``get_order_status`` tool: order header, items and customer name.

Tracking code and ETA are returned only when present (shipped/delivered).
Pending/confirmed orders get an explicit ``shipped=False`` so the agent states
what happens next instead of inventing a code.
"""

import sqlite3

from pydantic import BaseModel, Field

from emporio.llm.base import ToolDefinition


class GetOrderStatusArgs(BaseModel):
    """Typed arguments the model provides for an order lookup."""

    order_id: int = Field(description="Order id from the customer, e.g. 8.")


class OrderItem(BaseModel):
    """One line of the order with the product name resolved."""

    product_id: int
    name: str
    quantity: int
    unit_price_brl: float


class OrderStatus(BaseModel):
    """Order state, or a not-found marker for unknown ids."""

    found: bool
    order_id: int | None = None
    status: str | None = None
    customer_name: str | None = None
    total_brl: float | None = None
    payment_method: str | None = None
    shipped: bool = False
    tracking_code: str | None = None
    estimated_delivery: str | None = None
    items: list[OrderItem] = Field(default_factory=list)
    message: str | None = None


DEFINITION = ToolDefinition(
    name="get_order_status",
    description="Order status with items and customer name. Tracking only when shipped.",
    parameters=GetOrderStatusArgs.model_json_schema(),
)


def run(connection: sqlite3.Connection, args: GetOrderStatusArgs) -> OrderStatus:
    """Fetch the order; unknown ids return found=False instead of raising."""
    row = connection.execute(
        "SELECT o.order_id, o.status, cu.name, o.total_brl, o.payment_method, "
        "o.tracking_code, o.estimated_delivery "
        "FROM orders o, customers cu "
        "WHERE o.customer_id = cu.customer_id AND o.order_id = ?",
        (args.order_id,),
    ).fetchone()
    if row is None:
        return OrderStatus(found=False, message=f"Order {args.order_id} was not found.")
    item_rows = connection.execute(
        "SELECT i.product_id, p.name, i.quantity, p.price_brl "
        "FROM order_items i, products p "
        "WHERE i.product_id = p.product_id AND i.order_id = ?",
        (args.order_id,),
    ).fetchall()
    return OrderStatus(
        found=True,
        order_id=int(row[0]),
        status=str(row[1]),
        customer_name=str(row[2]),
        total_brl=float(row[3]) if row[3] is not None else None,
        payment_method=row[4],
        shipped=bool(row[5]),
        tracking_code=row[5],
        estimated_delivery=row[6],
        items=[
            OrderItem(
                product_id=int(item[0]),
                name=str(item[1]),
                quantity=int(item[2]),
                unit_price_brl=float(item[3]),
            )
            for item in item_rows
        ],
    )
