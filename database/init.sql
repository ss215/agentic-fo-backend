-- Database Initialization Script
-- Run this script to initialize the Agentic F&O Execution System database

-- Create database
CREATE DATABASE agentic_fo;

-- Connect to the database
\c agentic_fo;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create user for application
CREATE USER agentic_user WITH PASSWORD 'agentic_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agentic_fo TO agentic_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO agentic_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agentic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agentic_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO agentic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO agentic_user;

-- Run the main schema
\i schema.sql

-- Verify database creation
SELECT 'Database initialized successfully' as status;
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';
