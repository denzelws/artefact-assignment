"""CSV -> SQLite loader checks, including plan edge cases."""

import sqlite3
from pathlib import Path

import pytest

from emporio.data import connect, load_database

EXPECTED_COUNTS = {
    "categories": 9,
    "customers": 50,
    "products": 65,
    "orders": 20,
    "order_items": 22,
    "promotions": 25,
}


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_emporio.sqlite"


def test_load_counts(db_path: Path) -> None:
    assert load_database(db_path, "data") == EXPECTED_COUNTS


def test_plan_edge_cases(db_path: Path) -> None:
    load_database(db_path, "data")
    connection = connect(db_path)
    try:
        assert connection.execute("SELECT stock_quantity FROM products WHERE product_id=96").fetchone()[0] == 0
        assert connection.execute("SELECT status FROM products WHERE product_id=113").fetchone()[0] == "discontinued"
        assert connection.execute("SELECT status FROM products WHERE product_id=130").fetchone()[0] == "coming_soon"
        active = [
            row[0]
            for row in connection.execute(
                "SELECT promotion_id FROM promotions WHERE is_active=1 ORDER BY 1"
            )
        ]
        assert active == [12, 14, 19, 24]
    finally:
        connection.close()


def test_reload_is_idempotent(db_path: Path) -> None:
    first = load_database(db_path, "data")
    assert load_database(db_path, "data") == first


def test_missing_data_dir_raises(db_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_database(db_path, "missing_dir")


def test_foreign_keys_enforced(db_path: Path) -> None:
    load_database(db_path, "data")
    connection = connect(db_path)
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO products (product_id, price_brl, name, category_id, "
                "stock_quantity, status) VALUES (9999, 10.0, 'Ghost', 4242, 1, 'active')"
            )
    finally:
        connection.close()


def test_empty_tables_load_as_zero(db_path: Path, tmp_path: Path) -> None:
    from emporio.data.loader import FILENAMES

    headers = {
        "categories": "category_id,name,description",
        "customers": "customer_id,name,phone,email,city",
        "order_items": "order_id,quantity,product_id",
        "orders": "order_id,customer_id,order_date,status,total_brl,"
        "payment_method,tracking_code,estimated_delivery,notes",
        "products": "product_id,price_brl,name,category_id,description,"
        "stock_quantity,status,specs,created_at",
        "promotions": "promotion_id,product_id,discount_percent,description,is_active",
    }
    data_dir = tmp_path / "empty_data"
    data_dir.mkdir()
    for table, filename in FILENAMES.items():
        (data_dir / filename).write_text(headers[table] + "\n", encoding="utf-8")
    assert load_database(db_path, str(data_dir)) == dict.fromkeys(FILENAMES, 0)
