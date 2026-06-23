-- Demo rows. Idempotent via ON CONFLICT so re-running on startup is a no-op.

INSERT INTO demo.customers (id, name, email, country, created_at) VALUES
    (1, 'Alice Martin', 'alice@example.com',  'USA',    '2024-01-15'),
    (2, 'Bob Chen',     'bob@example.com',    'Canada', '2024-02-03'),
    (3, 'Carla Gomez',  'carla@example.com',  'Mexico', '2024-02-20'),
    (4, 'David Smith',  'david@example.com',  'USA',    '2024-03-11'),
    (5, 'Emma Wilson',  'emma@example.com',   'UK',     '2024-04-02')
ON CONFLICT (id) DO NOTHING;

INSERT INTO demo.products (id, name, category, price) VALUES
    (1, 'Wireless Mouse',              'Electronics', 25.00),
    (2, 'Mechanical Keyboard',         'Electronics', 80.00),
    (3, 'USB-C Cable',                 'Accessories', 12.00),
    (4, 'Laptop Stand',                'Accessories', 35.00),
    (5, 'Noise-Cancelling Headphones', 'Electronics', 199.00),
    (6, 'Desk Lamp',                   'Home',        45.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO demo.orders (id, customer_id, ordered_at, status) VALUES
    (1, 1, '2024-05-01', 'completed'),
    (2, 2, '2024-05-03', 'completed'),
    (3, 1, '2024-05-10', 'shipped'),
    (4, 3, '2024-05-12', 'completed'),
    (5, 4, '2024-05-15', 'cancelled'),
    (6, 5, '2024-05-20', 'completed')
ON CONFLICT (id) DO NOTHING;

INSERT INTO demo.order_items (id, order_id, product_id, quantity, unit_price) VALUES
    (1,  1, 1, 2, 25.00),
    (2,  1, 3, 1, 12.00),
    (3,  2, 5, 1, 199.00),
    (4,  2, 1, 1, 25.00),
    (5,  3, 2, 1, 80.00),
    (6,  3, 4, 2, 35.00),
    (7,  4, 6, 3, 45.00),
    (8,  5, 1, 1, 25.00),
    (9,  6, 5, 1, 199.00),
    (10, 6, 3, 2, 12.00)
ON CONFLICT (id) DO NOTHING;
