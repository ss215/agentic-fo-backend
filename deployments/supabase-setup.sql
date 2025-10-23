-- Supabase Database Setup for Agentic F&O Execution System
-- Run this script in Supabase SQL Editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- USER MANAGEMENT
-- =============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- =============================================
-- TRADING SESSIONS
-- =============================================

CREATE TABLE trading_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(100) NOT NULL,
    broker_type VARCHAR(20) NOT NULL, -- KITE, UPSTOX
    broker_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_paper_trading BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trading_sessions_user ON trading_sessions(user_id);
CREATE INDEX idx_trading_sessions_active ON trading_sessions(is_active);

-- =============================================
-- ORDERS MANAGEMENT (SEBI/NSE COMPLIANT)
-- =============================================

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trading_session_id UUID NOT NULL REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    -- Order identification
    client_order_id VARCHAR(100) UNIQUE NOT NULL,
    broker_order_id VARCHAR(100),
    
    -- Instrument details
    instrument_token VARCHAR(50) NOT NULL,
    instrument_name VARCHAR(100) NOT NULL,
    exchange VARCHAR(20) NOT NULL, -- NSE, BSE
    
    -- Order parameters
    order_type VARCHAR(20) NOT NULL, -- BUY, SELL
    product_type VARCHAR(20) NOT NULL, -- MIS, NRML, CNC
    variety VARCHAR(20) NOT NULL, -- regular, bracket, cover
    quantity INTEGER NOT NULL,
    price DECIMAL(15,2),
    trigger_price DECIMAL(15,2),
    
    -- Order status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, OPEN, COMPLETE, CANCELLED, REJECTED
    filled_quantity INTEGER DEFAULT 0,
    average_price DECIMAL(15,2),
    
    -- SEBI/NSE Compliance
    algo_id VARCHAR(50) NOT NULL, -- Required by exchanges
    strategy_name VARCHAR(100),
    risk_parameters JSONB,
    
    -- Timestamps
    order_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_timestamp TIMESTAMP,
    cancelled_timestamp TIMESTAMP,
    
    -- Broker response
    broker_response JSONB,
    error_message TEXT
);

-- Indexes for orders table
CREATE INDEX idx_orders_user_session ON orders(user_id, trading_session_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_timestamp ON orders(order_timestamp);
CREATE INDEX idx_orders_algo_id ON orders(algo_id);
CREATE INDEX idx_orders_client_id ON orders(client_order_id);
CREATE INDEX idx_orders_broker_id ON orders(broker_order_id);
CREATE INDEX idx_orders_instrument ON orders(instrument_token);

-- =============================================
-- ORDER FILLS
-- =============================================

CREATE TABLE order_fills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    fill_quantity INTEGER NOT NULL,
    fill_price DECIMAL(15,2) NOT NULL,
    fill_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    broker_fill_id VARCHAR(100)
);

CREATE INDEX idx_order_fills_order ON order_fills(order_id);
CREATE INDEX idx_order_fills_timestamp ON order_fills(fill_timestamp);

-- =============================================
-- POSITIONS
-- =============================================

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trading_session_id UUID NOT NULL REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    instrument_token VARCHAR(50) NOT NULL,
    instrument_name VARCHAR(100) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    
    -- Position details
    quantity INTEGER NOT NULL, -- Positive for long, negative for short
    average_price DECIMAL(15,2) NOT NULL,
    current_price DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2) DEFAULT 0.0,
    realized_pnl DECIMAL(15,2) DEFAULT 0.0,
    
    -- Risk metrics
    margin_used DECIMAL(15,2) DEFAULT 0.0,
    exposure DECIMAL(15,2) DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(trading_session_id, instrument_token)
);

CREATE INDEX idx_positions_session ON positions(trading_session_id);
CREATE INDEX idx_positions_instrument ON positions(instrument_token);
CREATE INDEX idx_positions_updated ON positions(updated_at);

-- =============================================
-- PORTFOLIO SNAPSHOTS
-- =============================================

CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trading_session_id UUID NOT NULL REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    -- Portfolio metrics
    total_value DECIMAL(15,2) NOT NULL,
    available_cash DECIMAL(15,2) NOT NULL,
    used_margin DECIMAL(15,2) NOT NULL,
    total_pnl DECIMAL(15,2) NOT NULL,
    day_pnl DECIMAL(15,2) NOT NULL,
    
    -- Risk metrics
    var_95 DECIMAL(15,2),
    max_drawdown DECIMAL(15,2),
    sharpe_ratio DECIMAL(10,4),
    
    -- Timestamp
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolio_session_timestamp ON portfolio_snapshots(trading_session_id, snapshot_timestamp);
CREATE INDEX idx_portfolio_timestamp ON portfolio_snapshots(snapshot_timestamp);

-- =============================================
-- RISK EVENTS
-- =============================================

CREATE TABLE risk_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trading_session_id UUID NOT NULL REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    event_type VARCHAR(50) NOT NULL, -- MARGIN_CALL, EXPOSURE_LIMIT, VAR_BREACH
    severity VARCHAR(20) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    message TEXT NOT NULL,
    parameters JSONB,
    
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_events_session ON risk_events(trading_session_id);
CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_severity ON risk_events(severity);
CREATE INDEX idx_risk_events_resolved ON risk_events(is_resolved);

-- =============================================
-- AUDIT LOGS (IMMUTABLE)
-- =============================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Audit details
    user_id UUID REFERENCES users(id),
    trading_session_id UUID REFERENCES trading_sessions(id),
    
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    
    -- Request details
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    -- Data changes
    old_values JSONB,
    new_values JSONB,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_session ON audit_logs(trading_session_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_timestamp ON audit_logs(created_at);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- =============================================
-- SYSTEM METRICS
-- =============================================

CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- System metrics
    cpu_usage DECIMAL(5,2) NOT NULL,
    memory_usage DECIMAL(5,2) NOT NULL,
    disk_usage DECIMAL(5,2) NOT NULL,
    
    -- Trading metrics
    orders_per_second DECIMAL(10,2) NOT NULL,
    active_orders INTEGER NOT NULL,
    total_orders INTEGER NOT NULL,
    
    -- API metrics
    api_response_time DECIMAL(10,2) NOT NULL,
    api_requests_per_second DECIMAL(10,2) NOT NULL,
    api_error_rate DECIMAL(5,2) NOT NULL,
    
    -- Timestamp
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON system_metrics(recorded_at);
CREATE INDEX idx_metrics_cpu ON system_metrics(cpu_usage);
CREATE INDEX idx_metrics_memory ON system_metrics(memory_usage);

-- =============================================
-- CONFIGURATIONS
-- =============================================

CREATE TABLE configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_config_key ON configurations(key);
CREATE INDEX idx_config_active ON configurations(is_active);

-- =============================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_sessions_updated_at BEFORE UPDATE ON trading_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE ON configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- SAMPLE DATA
-- =============================================

-- Insert default admin user
INSERT INTO users (username, email, hashed_password, is_admin) VALUES
('admin', 'admin@agentic-fo.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4.8.2', TRUE);

-- Insert default configuration
INSERT INTO configurations (key, value, description) VALUES
('system_name', '"Agentic F&O Execution System"', 'System name'),
('algo_id', '"AGENTIC_FO_001"', 'SEBI/NSE compliant algo ID'),
('strategy_name', '"AgenticF&OStrategy"', 'Default strategy name'),
('max_daily_loss', '100000.0', 'Maximum daily loss limit'),
('max_position_size', '1000000.0', 'Maximum position size limit'),
('max_margin_usage', '0.8', 'Maximum margin usage (80%)'),
('risk_check_interval', '60', 'Risk check interval in seconds'),
('order_timeout', '300', 'Order timeout in seconds');

-- =============================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_fills ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE configurations ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view their own trading sessions" ON trading_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own orders" ON orders
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own order fills" ON order_fills
    FOR SELECT USING (auth.uid() = (SELECT user_id FROM orders WHERE id = order_id));

CREATE POLICY "Users can view their own positions" ON positions
    FOR SELECT USING (auth.uid() = (SELECT user_id FROM trading_sessions WHERE id = trading_session_id));

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- Active positions view
CREATE VIEW active_positions AS
SELECT 
    p.*,
    t.session_name,
    u.username
FROM positions p
JOIN trading_sessions t ON p.trading_session_id = t.id
JOIN users u ON t.user_id = u.id
WHERE t.is_active = TRUE;

-- Order summary view
CREATE VIEW order_summary AS
SELECT 
    o.*,
    t.session_name,
    u.username,
    COUNT(of.id) as fill_count,
    COALESCE(SUM(of.fill_quantity), 0) as total_filled
FROM orders o
JOIN trading_sessions t ON o.trading_session_id = t.id
JOIN users u ON t.user_id = u.id
LEFT JOIN order_fills of ON o.id = of.order_id
GROUP BY o.id, t.session_name, u.username;

-- Portfolio summary view
CREATE VIEW portfolio_summary AS
SELECT 
    ps.*,
    t.session_name,
    u.username
FROM portfolio_snapshots ps
JOIN trading_sessions t ON ps.trading_session_id = t.id
JOIN users u ON t.user_id = u.id
WHERE ps.snapshot_timestamp = (
    SELECT MAX(snapshot_timestamp) 
    FROM portfolio_snapshots ps2 
    WHERE ps2.trading_session_id = ps.trading_session_id
);

-- =============================================
-- COMMENTS
-- =============================================

COMMENT ON TABLE users IS 'User management and authentication';
COMMENT ON TABLE trading_sessions IS 'Trading session management with broker configuration';
COMMENT ON TABLE orders IS 'Order management with SEBI/NSE compliance and algo-id tagging';
COMMENT ON TABLE order_fills IS 'Order fill details and execution records';
COMMENT ON TABLE positions IS 'Current trading positions and P&L tracking';
COMMENT ON TABLE portfolio_snapshots IS 'Historical portfolio snapshots for analysis';
COMMENT ON TABLE risk_events IS 'Risk management events and alerts';
COMMENT ON TABLE audit_logs IS 'Immutable audit trail for compliance';
COMMENT ON TABLE system_metrics IS 'System performance and trading metrics';
COMMENT ON TABLE configurations IS 'System configuration parameters';

COMMENT ON COLUMN orders.algo_id IS 'SEBI/NSE compliant algorithm identifier';
COMMENT ON COLUMN orders.strategy_name IS 'Trading strategy name for reporting';
COMMENT ON COLUMN orders.risk_parameters IS 'Risk management parameters for the order';
COMMENT ON COLUMN audit_logs.old_values IS 'Previous values before change (for audit)';
COMMENT ON COLUMN audit_logs.new_values IS 'New values after change (for audit)';

-- =============================================
-- END OF SUPABASE SETUP
-- =============================================

-- Schema creation complete for Supabase
-- This script sets up the complete database schema
-- for the Agentic F&O Execution System on Supabase
