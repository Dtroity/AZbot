-- Initialize database with extensions and basic setup
-- This file is automatically executed when the database container starts

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set up full-text search configuration
CREATE TEXT SEARCH CONFIGURATION russian (COPY = simple);

-- Create indexes for better performance
-- These will be created after the tables are created by SQLAlchemy

-- Order text search index
-- CREATE INDEX IF NOT EXISTS idx_orders_text_gin ON orders USING gin(to_tsvector('russian', text));

-- Order status index
-- CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Order created_at index
-- CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Supplier telegram_id index
-- CREATE INDEX IF NOT EXISTS idx_suppliers_telegram_id ON suppliers(telegram_id);

-- Filter keyword index
-- CREATE INDEX IF NOT EXISTS idx_filters_keyword ON filters(keyword);

-- Activity log created_at index
-- CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);

-- Activity log user_id index
-- CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);

-- Order messages order_id index
-- CREATE INDEX IF NOT EXISTS idx_order_messages_order_id ON order_messages(order_id);

-- Composite indexes for common queries
-- CREATE INDEX IF NOT EXISTS idx_orders_supplier_status ON orders(supplier_id, status);
-- CREATE INDEX IF NOT EXISTS idx_filters_supplier_active ON filters(supplier_id, active);

-- Set up database statistics
-- ANALYZE;
