"""CSV -> SQLite loader for the store datasets.

Reads the provided ``data/*.csv`` files (never renamed, per plan) and loads
them into a local SQLite database with typed columns and foreign keys.
Uses only the standard library (``sqlite3``, ``csv``).

Idempotent: every load drops and recreates the tables inside one transaction.
"""

import csv
import sqlite3
from pathlib import Path

# Exact provided filenames (plan section 2: do not rename).
FILENAMES = {
    "categories": "desafio_tecnico_ai_eng - categories.csv",
    "customers": "desafio_tecnico_ai_eng - customers.csv",
    "order_items": "desafio_tecnico_ai_eng - order_items.csv",
    "orders": "desafio_tecnico_ai_eng - orders.csv",
    "products": "desafio_tecnico_ai_eng - products.csv",
    "promotions": "desafio_tecnico_ai_eng - promotions.csv",
}

SCHEMA = """
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    price_brl REAL NOT NULL,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories (category_id),
    description TEXT,
    stock_quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    specs TEXT,
    created_at TEXT
);
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    city TEXT
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date TEXT,
    status TEXT NOT NULL,
    total_brl REAL,
    payment_method TEXT,
    tracking_code TEXT,
    estimated_delivery TEXT,
    notes TEXT
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders (order_id),
    quantity INTEGER NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    PRIMARY KEY (order_id, product_id)
);
CREATE TABLE promotions (
    promotion_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    discount_percent REAL NOT NULL,
    description TEXT,
    is_active INTEGER NOT NULL
);
CREATE INDEX idx_products_category ON products (category_id);
CREATE INDEX idx_products_status ON products (status);
CREATE INDEX idx_orders_status ON orders (status);
"""

# Column converters: empty string -> None (NULL), otherwise typed value.
_INT_COLUMNS = {
    "categories": {"category_id"},
    "products": {"product_id", "category_id", "stock_quantity"},
    "customers": {"customer_id"},
    "orders": {"order_id", "customer_id"},
    "order_items": {"order_id", "quantity", "product_id"},
    "promotions": {"promotion_id", "product_id", "is_active"},
}
_REAL_COLUMNS = {
    "products": {"price_brl"},
    "orders": {"total_brl"},
    "promotions": {"discount_percent"},
}


def _convert(table: str, column: str, value: str) -> object:
    """Convert one raw CSV string to its typed value (or None for blanks)."""
    if value == "":
        return None
    if column in _INT_COLUMNS.get(table, set()):
        return int(value)
    if column in _REAL_COLUMNS.get(table, set()):
        return float(value)
    return value


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open the SQLite database with FK enforcement and dict-like rows."""
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def load_database(
    db_path: str | Path = "emporio.sqlite",
    data_dir: str | Path = "data",
) -> dict[str, int]:
    """Load all CSVs into ``db_path``; return ``{table: row_count}``.

    Raises :class:`FileNotFoundError` if a CSV is missing and
    :class:`sqlite3.IntegrityError` if the data violates the schema.
    """
    data_dir = Path(data_dir)
    load_order = ["categories", "customers", "products", "orders", "order_items", "promotions"]
    staged: dict[str, list[dict[str, object]]] = {}
    for table in load_order:
        csv_path = data_dir / FILENAMES[table]
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing dataset (do not rename files): {csv_path}")
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            staged[table] = [
                {column: _convert(table, column, value) for column, value in row.items()}
                for row in csv.DictReader(handle)
            ]

    db_path = Path(db_path)
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    # Drops run child-first so FK enforcement never blocks a reload;
    # inserts run parent-first so FK references always exist.
    drop_order = list(reversed(load_order))
    with connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.executescript(
            "\n".join(f"DROP TABLE IF EXISTS {table};" for table in drop_order) + "\n" + SCHEMA
        )
        connection.execute("PRAGMA foreign_keys = ON")
        for table in load_order:
            rows = staged[table]
            if not rows:
                counts[table] = 0
                continue
            columns = list(rows[0].keys())
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                [[row[column] for column in columns] for row in rows],
            )
            counts[table] = len(rows)
    return counts
