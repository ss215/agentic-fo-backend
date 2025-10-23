# 🚀 Agentic F&O Backend API

## 📋 **Overview**

Production-ready backend API for the Agentic F&O Execution System - a comprehensive Indian derivatives trading platform with SEBI/NSE compliance, real-time monitoring, and enterprise-grade features.

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chrome        │    │   Backend API   │    │   Database      │
│   Extension     │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│                 │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   Port: 6379    │
                       └─────────────────┘
```

## 🚀 **Quick Start**

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python -c "from database.connection import create_tables; create_tables()"

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Docker Deployment**
```bash
# Build and run with Docker Compose
docker-compose -f deployments/docker-compose.yml up --build

# Or run individual services
docker-compose -f deployments/docker-compose.yml up postgres redis backend
```

### **Cloud Deployment**
- **Render.com**: See `deployments/render.yaml`
- **Supabase**: See `deployments/supabase-setup.sql`
- **AWS/GCP/Azure**: See deployment guides

## 📊 **API Endpoints**

### **Trading API** (`/api/v1/trading/`)
- `GET /health` - Trading system health
- `GET /metrics` - Real-time trading metrics
- `POST /orders` - Create trading orders
- `GET /orders` - Get order history
- `GET /positions` - Get current positions
- `GET /portfolio` - Get portfolio summary
- `POST /halt` - Emergency halt trading
- `POST /resume` - Resume trading
- `WS /ws` - WebSocket for real-time data

### **Authentication API** (`/api/v1/auth/`)
- `POST /login` - User authentication
- `POST /logout` - User logout
- `POST /refresh` - Token refresh

### **Monitoring API** (`/api/v1/monitoring/`)
- `GET /health` - System health check
- `GET /metrics` - System performance metrics

### **Admin API** (`/api/v1/admin/`)
- `GET /config` - System configuration
- `GET /users` - User management
- `GET /audit-logs` - Audit trail access

## 🗄️ **Database Schema**

### **Core Tables**
- **users** - User management and authentication
- **trading_sessions** - Trading session management
- **orders** - Order management (SEBI/NSE compliant)
- **order_fills** - Order execution details
- **positions** - Current trading positions
- **portfolio_snapshots** - Historical portfolio data
- **risk_events** - Risk management events
- **audit_logs** - Immutable audit trail
- **system_metrics** - Performance metrics
- **configurations** - System configuration

### **Key Features**
- ✅ **SEBI/NSE Compliance** - Algo-ID tagging, audit trails
- ✅ **Risk Management** - VaR, drawdown, exposure tracking
- ✅ **Order Management** - Complete order lifecycle
- ✅ **Portfolio Tracking** - Real-time P&L monitoring
- ✅ **Audit Logging** - Immutable compliance records
- ✅ **Performance Monitoring** - System metrics tracking

## 🔧 **Configuration**

### **Environment Variables**
```env
# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agentic_fo

# Redis
REDIS_URL=redis://localhost:6379/0

# Broker APIs
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
UPSTOX_API_KEY=your_upstox_api_key
UPSTOX_API_SECRET=your_upstox_api_secret

# Model API
MODEL_API_URL=https://your-model-api.com/v1
MODEL_API_KEY=your_model_api_key

# Security
SECRET_KEY=your-secret-key-change-in-production

# Algo ID (SEBI/NSE Compliance)
ALGO_ID=AGENTIC_FO_001
STRATEGY_NAME=AgenticF&OStrategy

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

## 🚀 **Deployment Options**

### **1. Local Development**
```bash
python app/main.py
```

### **2. Docker**
```bash
docker-compose -f deployments/docker-compose.yml up --build
```

### **3. Render.com**
- Use `deployments/render.yaml` configuration
- Connect GitHub repository
- Set environment variables

### **4. Supabase**
- Run `deployments/supabase-setup.sql` in SQL Editor
- Use Supabase connection string

### **5. AWS/GCP/Azure**
- Use Docker containers
- Configure load balancers
- Set up monitoring

## 📈 **Monitoring & Logging**

### **Health Checks**
- **API Health**: `/health`
- **Trading Health**: `/api/v1/trading/health`
- **System Metrics**: `/api/v1/monitoring/metrics`

### **Logging**
- **Structured Logging** with 7 different log streams
- **Audit Trails** for compliance
- **Error Tracking** with context
- **Performance Monitoring** with metrics

### **Metrics**
- **Prometheus** integration
- **Grafana** dashboards
- **Real-time** monitoring
- **Alerting** system

## 🔒 **Security Features**

### **API Security**
- ✅ JWT token authentication
- ✅ Rate limiting (100 req/min)
- ✅ CORS configuration
- ✅ Input validation
- ✅ SQL injection prevention

### **Database Security**
- ✅ Encrypted connections
- ✅ User access controls
- ✅ Audit logging
- ✅ Backup encryption

### **Compliance**
- ✅ SEBI/NSE algo-id tagging
- ✅ Immutable audit logs
- ✅ Risk management controls
- ✅ Order tracking and reporting

## 🧪 **Testing**

### **Run Tests**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests
pytest

# With coverage
pytest --cov=app
```

### **Test Coverage**
- **Unit Tests**: >70% coverage
- **Integration Tests**: API endpoints
- **Performance Tests**: Load testing
- **Security Tests**: Vulnerability scanning

## 📚 **Documentation**

### **API Documentation**
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### **Code Documentation**
- **Docstrings** for all functions
- **Type Hints** for better IDE support
- **Comments** for complex logic
- **README** files for each module

## 🤝 **Contributing**

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### **Code Standards**
- **Python**: PEP 8 style guide
- **Type Hints**: Use type annotations
- **Docstrings**: Google style docstrings
- **Testing**: Write tests for new features

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

### **Documentation**
- **API Docs**: `/docs` endpoint
- **Deployment Guides**: `deployments/` folder
- **Database Schema**: `database/schema.sql`

### **Issues**
- **Bug Reports**: GitHub Issues
- **Feature Requests**: GitHub Discussions
- **Security Issues**: Private contact

## 🎯 **Roadmap**

### **Current Features**
- ✅ Real-time trading API
- ✅ SEBI/NSE compliance
- ✅ Risk management
- ✅ Portfolio tracking
- ✅ Audit logging
- ✅ WebSocket support

### **Upcoming Features**
- 🔄 Machine learning integration
- 🔄 Advanced analytics
- 🔄 Multi-broker support
- 🔄 Mobile app API
- 🔄 Advanced risk models

---

**🚀 Ready for production trading at enterprise scale!**
