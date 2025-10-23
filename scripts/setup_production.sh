#!/bin/bash

echo "🚀 Setting up Agentic F&O Execution System for Production"
echo "========================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cat > .env << EOF
# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://agentic_user:agentic_password@postgres:5432/agentic_fo

# Redis
REDIS_URL=redis://redis:6379/0

# Broker APIs (Update these with your actual keys)
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
UPSTOX_API_KEY=your_upstox_api_key
UPSTOX_API_SECRET=your_upstox_api_secret

# Model API
MODEL_API_URL=https://your-model-api.com/v1
MODEL_API_KEY=your_model_api_key

# Security
SECRET_KEY=$(openssl rand -hex 32)

# Algo ID (SEBI/NSE Compliance)
ALGO_ID=AGENTIC_FO_001
STRATEGY_NAME=AgenticF&OStrategy

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/prometheus
mkdir -p data/grafana

echo "✅ Directories created"

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose -f deployments/docker-compose.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check database
if docker exec agentic_fo_postgres pg_isready -U agentic_user -d agentic_fo > /dev/null 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ Database is not ready"
fi

# Check Redis
if docker exec agentic_fo_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check backend API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is ready"
else
    echo "❌ Backend API is not ready"
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is ready"
else
    echo "❌ Prometheus is not ready"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is ready"
else
    echo "❌ Grafana is not ready"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "📊 Access Points:"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/admin123)"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update Chrome extension config.js with your API URL"
echo "   2. Configure your broker API keys in .env file"
echo "   3. Set up monitoring alerts in Grafana"
echo "   4. Test the system with the Chrome extension"
echo ""
echo "📋 Useful Commands:"
echo "   - View logs: docker-compose -f deployments/docker-compose.yml logs"
echo "   - Stop services: docker-compose -f deployments/docker-compose.yml down"
echo "   - Restart services: docker-compose -f deployments/docker-compose.yml restart"
echo "   - Update services: docker-compose -f deployments/docker-compose.yml up --build -d"
echo ""
echo "🚀 Your Agentic F&O Execution System is ready for production!"
