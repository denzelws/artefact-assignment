"""Shared pricing rules for product-facing tools.

Single source of truth for the manual rules the model must never compute itself:
- Active promo -> promotional price; PIX 5% does NOT stack (``pix_eligible=False``).
- No promo -> PIX 5% off the table price is available (``pix_eligible=True``).
"""

import sqlite3

PIX_DISCOUNT = 0.05


def price_block(
    connection: sqlite3.Connection, product_id: int, price_brl: float
) -> dict[str, object]:
    """Return promo/pix fields for one product (active promos only)."""
    row = connection.execute(
        "SELECT discount_percent FROM promotions WHERE product_id = ? AND is_active = 1",
        (product_id,),
    ).fetchone()
    if row is None:
        return {
            "promo_price": None,
            "pix_eligible": True,
            "pix_price": round(price_brl * (1 - PIX_DISCOUNT), 2),
        }
    return {
        "promo_price": round(price_brl * (1 - float(row[0]) / 100), 2),
        "pix_eligible": False,
        "pix_price": None,
    }
