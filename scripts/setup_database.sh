#!/bin/bash

echo "🗄️ Setting up Agentic F&O Database"
echo "==================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo "   Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "   macOS: brew install postgresql"
    echo "   CentOS/RHEL: sudo yum install postgresql postgresql-server"
    exit 1
fi

echo "✅ PostgreSQL is available"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   Ubuntu/Debian: sudo systemctl start postgresql"
    echo "   macOS: brew services start postgresql"
    echo "   CentOS/RHEL: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database and user
echo "📝 Creating database and user..."

# Run as postgres user
sudo -u postgres psql -c "CREATE DATABASE agentic_fo;" 2>/dev/null || echo "Database may already exist"
sudo -u postgres psql -c "CREATE USER agentic_user WITH PASSWORD 'agentic_password';" 2>/dev/null || echo "User may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE agentic_fo TO agentic_user;" 2>/dev/null

echo "✅ Database and user created"

# Run schema creation
echo "📋 Creating database schema..."
cd "$(dirname "$0")/.."
psql -h localhost -U agentic_user -d agentic_fo -f database/schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Database schema created successfully"
else
    echo "❌ Failed to create database schema"
    exit 1
fi

# Verify database setup
echo "🔍 Verifying database setup..."
TABLE_COUNT=$(psql -h localhost -U agentic_user -d agentic_fo -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

echo "📊 Database Statistics:"
echo "   - Tables created: $TABLE_COUNT"
echo "   - Database: agentic_fo"
echo "   - User: agentic_user"
echo "   - Host: localhost"
echo "   - Port: 5432"

# Test connection
echo "🧪 Testing database connection..."
if psql -h localhost -U agentic_user -d agentic_fo -c "SELECT 'Connection successful' as status;" > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

echo ""
echo "🎉 Database setup complete!"
echo ""
echo "📋 Connection Details:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: agentic_fo"
echo "   - Username: agentic_user"
echo "   - Password: agentic_password"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update your .env file with database connection details"
echo "   2. Start the backend API server"
echo "   3. Test the connection with the Chrome extension"
echo ""
echo "📊 Database Schema:"
echo "   - users: User management"
echo "   - trading_sessions: Trading session management"
echo "   - orders: Order management (SEBI/NSE compliant)"
echo "   - order_fills: Order execution details"
echo "   - positions: Current trading positions"
echo "   - portfolio_snapshots: Historical portfolio data"
echo "   - risk_events: Risk management events"
echo "   - audit_logs: Immutable audit trail"
echo "   - system_metrics: Performance metrics"
echo "   - configurations: System configuration"
echo ""
echo "🚀 Your database is ready for production trading!"
