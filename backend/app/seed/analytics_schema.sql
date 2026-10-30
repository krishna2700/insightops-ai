-- Sample business dataset the NL->SQL engine queries. Owned by the main `insightops`
-- role (which created the `analytics` schema), readable only by `analytics_readonly`.

CREATE TABLE IF NOT EXISTS analytics.customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    segment TEXT NOT NULL,       -- SMB | Mid-Market | Enterprise
    country TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    cost NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES analytics.customers(id),
    order_date DATE NOT NULL,
    status TEXT NOT NULL,        -- completed | refunded | cancelled
    total_amount NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES analytics.orders(id),
    product_id INTEGER NOT NULL REFERENCES analytics.products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON analytics.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON analytics.orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON analytics.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON analytics.order_items(product_id);
