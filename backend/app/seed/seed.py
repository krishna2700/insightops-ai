"""Seeds the `analytics` sample dataset: a realistic SaaS e-commerce business --
customers, products, orders, and order line items spanning ~2 years, with seasonal
(holiday) order volume and a gentle month-over-month growth trend. Enough real signal
for questions like "monthly revenue trend", "top products by revenue", or "average
order value by customer segment" to have genuinely interesting answers.

Run with: python -m app.seed.seed
"""

import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker
from sqlalchemy import create_engine, text

from app.config import get_settings

fake = Faker()
random.seed(42)
Faker.seed(42)

SEGMENTS = ["SMB", "SMB", "SMB", "Mid-Market", "Mid-Market", "Enterprise"]
COUNTRIES = ["United States", "United Kingdom", "Canada", "Germany", "Australia", "India", "France", "Brazil"]

CATEGORIES = {
    "Electronics": (29.99, 899.99),
    "Apparel": (14.99, 149.99),
    "Home & Garden": (9.99, 299.99),
    "Sports & Outdoors": (12.99, 399.99),
    "Books": (7.99, 39.99),
    "Beauty": (6.99, 89.99),
}

NUM_CUSTOMERS = 320
PRODUCTS_PER_CATEGORY = 7
MONTHS_OF_HISTORY = 24
ORDER_STATUSES = ["completed"] * 8 + ["refunded"] + ["cancelled"]


def seasonal_weight(d: date) -> float:
    """Holiday bump in Nov/Dec, slower in Jan/Feb, mild month-over-month growth trend."""
    month_weight = {11: 1.6, 12: 1.9, 1: 0.7, 2: 0.75}.get(d.month, 1.0)
    months_ago = (date.today().year - d.year) * 12 + (date.today().month - d.month)
    growth = max(0.6, 1.0 - months_ago * 0.015)
    return month_weight * growth


def generate_customers() -> list[dict]:
    customers = []
    start = date.today() - timedelta(days=365 * 3)
    for _ in range(NUM_CUSTOMERS):
        signup = fake.date_between(start_date=start, end_date=date.today() - timedelta(days=1))
        customers.append(
            {
                "name": fake.name(),
                "email": fake.unique.email(),
                "segment": random.choice(SEGMENTS),
                "country": random.choice(COUNTRIES),
                "signup_date": signup,
            }
        )
    return customers


def generate_products() -> list[dict]:
    products = []
    for category, (lo, hi) in CATEGORIES.items():
        for _ in range(PRODUCTS_PER_CATEGORY):
            price = round(random.uniform(lo, hi), 2)
            cost = round(price * random.uniform(0.35, 0.65), 2)
            products.append(
                {
                    "name": f"{fake.word().capitalize()} {category.split(' ')[0]} {fake.word().capitalize()}",
                    "category": category,
                    "price": price,
                    "cost": cost,
                }
            )
    return products


def generate_orders_and_items(
    customer_ids: list[int], customer_signup: dict[int, date], products: list[dict]
) -> tuple[list[dict], list[dict]]:
    orders: list[dict] = []
    items: list[dict] = []

    today = date.today()
    day_cursor = today - timedelta(days=30 * MONTHS_OF_HISTORY)

    while day_cursor <= today:
        weight = seasonal_weight(day_cursor)
        orders_today = max(0, int(random.gauss(mu=4 * weight, sigma=2)))

        for _ in range(orders_today):
            eligible = [cid for cid in customer_ids if customer_signup[cid] <= day_cursor]
            if not eligible:
                day_cursor += timedelta(days=1)
                continue
            customer_id = random.choice(eligible)
            status = random.choice(ORDER_STATUSES)

            num_items = random.randint(1, 5)
            chosen_products = random.sample(products, k=min(num_items, len(products)))
            order_total = 0.0
            order_item_rows = []
            for product in chosen_products:
                quantity = random.randint(1, 3)
                unit_price = product["price"]
                order_total += quantity * unit_price
                order_item_rows.append(
                    {"product_id": product["id"], "quantity": quantity, "unit_price": unit_price}
                )

            orders.append(
                {
                    "customer_id": customer_id,
                    "order_date": day_cursor,
                    "status": status,
                    "total_amount": round(order_total, 2),
                }
            )
            items.append(order_item_rows)  # aligned by index with `orders`

        day_cursor += timedelta(days=1)

    return orders, items


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)

    schema_sql = Path(__file__).with_name("analytics_schema.sql").read_text()

    with engine.begin() as conn:
        print("Creating analytics schema/tables...")
        for statement in schema_sql.split(";"):
            if statement.strip():
                conn.execute(text(statement))

        print("Clearing existing demo data...")
        conn.execute(text("TRUNCATE analytics.order_items, analytics.orders, analytics.products, analytics.customers RESTART IDENTITY CASCADE"))

        print(f"Inserting {NUM_CUSTOMERS} customers...")
        customers = generate_customers()
        conn.execute(
            text(
                "INSERT INTO analytics.customers (name, email, segment, country, signup_date) "
                "VALUES (:name, :email, :segment, :country, :signup_date)"
            ),
            customers,
        )
        rows = conn.execute(text("SELECT id, signup_date FROM analytics.customers ORDER BY id")).fetchall()
        ids = [r[0] for r in rows]
        signup_by_id = {r[0]: r[1] for r in rows}

        print("Inserting products...")
        products = generate_products()
        conn.execute(
            text(
                "INSERT INTO analytics.products (name, category, price, cost) "
                "VALUES (:name, :category, :price, :cost)"
            ),
            products,
        )
        product_rows = conn.execute(text("SELECT id, price FROM analytics.products ORDER BY id")).fetchall()
        products_with_ids = [{"id": r[0], "price": float(r[1])} for r in product_rows]

        print("Generating orders + line items (this models ~2 years of history)...")
        orders, items_by_order = generate_orders_and_items(ids, signup_by_id, products_with_ids)

        print(f"Inserting {len(orders)} orders...")
        conn.execute(
            text(
                "INSERT INTO analytics.orders (customer_id, order_date, status, total_amount) "
                "VALUES (:customer_id, :order_date, :status, :total_amount)"
            ),
            orders,
        )
        order_ids = [r[0] for r in conn.execute(text("SELECT id FROM analytics.orders ORDER BY id")).fetchall()]

        item_rows = []
        for order_id, item_group in zip(order_ids, items_by_order, strict=True):
            for item in item_group:
                item_rows.append({"order_id": order_id, **item})

        print(f"Inserting {len(item_rows)} order line items...")
        conn.execute(
            text(
                "INSERT INTO analytics.order_items (order_id, product_id, quantity, unit_price) "
                "VALUES (:order_id, :product_id, :quantity, :unit_price)"
            ),
            item_rows,
        )

    print("Done. Sample dataset ready in the `analytics` schema.")


if __name__ == "__main__":
    main()
