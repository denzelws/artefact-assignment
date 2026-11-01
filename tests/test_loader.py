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
