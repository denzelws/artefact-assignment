"""Store tool checks against the real seeded datasets."""

import json
import sqlite3
from pathlib import Path

import pytest

from emporio.data import load_database
from emporio.tools import TOOLS, execute_tool, get_tool_definitions


@pytest.fixture()
def connection(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "tools.sqlite"
    load_database(db_path, "data")
    from emporio.data import connect

    conn = connect(db_path)
    yield conn
    conn.close()


def test_six_tools_registered() -> None:
    assert sorted(TOOLS) == sorted(
        [
            "search_products",
            "get_product",
            "get_order_status",
            "get_promotions",
            "search_policies",
            "get_store_info",
        ]
    )
    assert len(get_tool_definitions()) == 6


def test_violoes_under_1000(connection: sqlite3.Connection) -> None:
    from emporio.tools import search_products

    results = search_products.run(
        connection,
        search_products.SearchProductsArgs(category="violões", max_price=1000, limit=50),
    )
    assert len(results) == 14
    assert all(item.category == "Violões" and item.price_brl <= 1000 for item in results)


def test_category_matches_without_accent(connection: sqlite3.Connection) -> None:
    from emporio.tools import search_products

    accented = search_products.run(connection, search_products.SearchProductsArgs(category="violões"))
    plain = search_products.run(connection, search_products.SearchProductsArgs(category="violoes"))
    by_id = search_products.run(connection, search_products.SearchProductsArgs(category="5"))
    assert len(accented) == len(plain) == len(by_id) > 0
    assert search_products.run(connection, search_products.SearchProductsArgs(category="nope")) == []


def test_takamine_price_and_pix(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_product

    detail = get_product.run(connection, get_product.GetProductArgs(product_id=95))
    assert detail.found and detail.price_brl == 2199.0
    assert detail.pix_eligible and detail.promo_price is None
    assert detail.pix_price == round(2199.0 * 0.95, 2)


def test_status_edge_cases_visible(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_product

    zero = get_product.run(connection, get_product.GetProductArgs(product_id=96))
    assert zero.found and zero.stock_quantity == 0 and zero.status == "active"
    assert get_product.run(connection, get_product.GetProductArgs(product_id=113)).status == "discontinued"
    assert get_product.run(connection, get_product.GetProductArgs(product_id=130)).status == "coming_soon"
    assert not get_product.run(connection, get_product.GetProductArgs(product_id=424242)).found


def test_in_stock_only_hides_zero_stock(connection: sqlite3.Connection) -> None:
    from emporio.tools import search_products

    args = search_products.SearchProductsArgs(query="Yamaha C40", in_stock_only=True)
    assert all(item.stock_quantity > 0 and item.status == "active" for item in search_products.run(connection, args))


def test_shipped_order_has_tracking(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_order_status

    order = get_order_status.run(connection, get_order_status.GetOrderStatusArgs(order_id=8))
    assert order.found and order.shipped
    assert order.tracking_code == "BRJL5544332BR" and order.estimated_delivery is not None
    assert order.customer_name is not None and order.items != []


def test_pending_order_has_no_tracking(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_order_status

    order = get_order_status.run(connection, get_order_status.GetOrderStatusArgs(order_id=13))
    assert order.found and not order.shipped
    assert order.tracking_code is None and order.estimated_delivery is None


def test_multi_item_and_cancelled_orders(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_order_status

    multi = get_order_status.run(connection, get_order_status.GetOrderStatusArgs(order_id=15))
    assert multi.found and len(multi.items) == 2
    cancelled = get_order_status.run(connection, get_order_status.GetOrderStatusArgs(order_id=20))
    assert cancelled.found and cancelled.status == "cancelled" and len(cancelled.items) == 2
    assert not get_order_status.run(connection, get_order_status.GetOrderStatusArgs(order_id=424242)).found


def test_only_active_promos_with_final_price(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_promotions

    promos = get_promotions.run(connection, get_promotions.GetPromotionsArgs())
    assert [promo.promotion_id for promo in promos] == [12, 14, 19, 24]
    for promo in promos:
        assert promo.pix_eligible is False
        assert promo.promo_price_brl == round(
            promo.original_price_brl * (1 - promo.discount_percent / 100), 2
        )
    single = get_promotions.run(connection, get_promotions.GetPromotionsArgs(product_id=127))
    assert len(single) == 1 and single[0].promotion_id == 12


def test_policy_and_store_wrappers(connection: sqlite3.Connection) -> None:
    from emporio.tools import get_store_info, search_policies

    hits = search_policies.run(connection, search_policies.SearchPoliciesArgs(query="troca"))
    assert hits and hits[0].id == "trocas_devolucoes"
    info = get_store_info.run(connection, get_store_info.GetStoreInfoArgs())
    assert info.phone_whatsapp == "(67) 3321-4500"


def test_execute_tool_json_envelope(connection: sqlite3.Connection) -> None:
    payload = json.loads(execute_tool("search_products", connection, {"query": "ukulele", "limit": 2}))
    assert payload["ok"] and len(payload["result"]) <= 2
    assert json.loads(execute_tool("nope", connection, {}))["ok"] is False
    bad = json.loads(execute_tool("get_product", connection, {"product_id": "abc"}))
    assert bad["ok"] is False
