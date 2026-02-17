# Supply Management System

Enterprise-level supply management system built with Telegram bot, FastAPI backend, PostgreSQL, Redis, and React dashboard.

## 🏗️ Architecture

```
┌────────────────────┐
│   Web Dashboard    │
│    React + API     │
└─────────┬──────────┘
          │
    FastAPI Backend
          │
┌─────────┼───────────┐
│         │           │
Telegram Bot   PostgreSQL    Redis
aiogram 3       database      cache
```

## ✨ Features

### Telegram Bot (Enterprise)
- ✅ Order distribution with intelligent routing
- ✅ Inline buttons for quick actions
- ✅ Threaded messaging support
- ✅ Multi-admin functionality
- ✅ Supplier role management
- ✅ Order status tracking
- ✅ Search functionality
- ✅ Activity history

### Web Dashboard
- ✅ Suppliers CRUD operations
- ✅ Filters management
- ✅ Live order view
- ✅ Order status management
- ✅ Analytics and statistics
- ✅ Activity logs

### PostgreSQL
- ✅ High performance
- ✅ Scalable architecture
- ✅ Safe transactions
- ✅ Full-text search

### Redis
- ✅ Fast caching
- ✅ FSM state management
- ✅ Real-time data

### Docker
- ✅ Simple deployment
- ✅ Production ready
- ✅ Health checks
- ✅ Load balancing with Nginx

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Telegram Bot Token
- Git

### 1. Clone the repository
```bash
git clone <repository-url>
cd AZbot
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start the system
```bash
docker-compose up -d
```

### 4. Initialize the database
```bash
docker-compose exec api python -c "from api.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Access the services
- **Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
supply-system/
│
├ bot/                    # Telegram bot
│   ├ main.py            # Bot entry point
│   ├ handlers/          # Bot handlers
│   ├ services/          # Business logic
│   ├ keyboards/         # Inline keyboards
│   ├ config.py          # Bot configuration
│   ├ database.py        # Database connection
│   ├ redis_client.py    # Redis client
│   └── cache.py         # Caching service
│
├ api/                   # FastAPI backend
│   ├ main.py           # API entry point
│   ├ routes/           # API routes
│   ├ models/           # Pydantic models
│   ├ dependencies.py   # Dependencies
│   └── config.py       # API configuration
│
├ dashboard/             # React dashboard
│   ├ src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Dashboard pages
│   │   └── services/    # API services
│   ├── package.json
│   └── Dockerfile
│
├ db/                    # Database models
│   └── models.py        # SQLAlchemy models
│
├ nginx/                 # Nginx configuration
│   └── nginx.conf
│
├ docker-compose.yml     # Docker composition
├ Dockerfile.bot         # Bot Dockerfile
├ Dockerfile.api         # API Dockerfile
├ .env.example          # Environment template
└── README.md           # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | Required |
| `ADMINS` | Admin Telegram IDs (comma-separated) | Required |
| `POSTGRES_DB` | Database name | `supply` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `API_PORT` | API port | `8000` |
| `SECRET_KEY` | JWT secret key | Required |

### Database Setup

The system uses PostgreSQL with the following tables:
- `suppliers` - Supplier information
- `filters` - Order routing filters
- `orders` - Order management
- `order_messages` - Order communication
- `activity_logs` - System activity tracking

## 📊 API Documentation

### Main Endpoints

#### Orders
- `GET /orders` - List orders with filtering
- `POST /orders` - Create new order
- `GET /orders/{id}` - Get order details
- `PUT /orders/{id}` - Update order
- `DELETE /orders/{id}` - Delete order

#### Suppliers
- `GET /suppliers` - List suppliers
- `POST /suppliers` - Create supplier
- `PUT /suppliers/{id}` - Update supplier
- `DELETE /suppliers/{id}` - Delete supplier

#### Filters
- `GET /filters` - List filters
- `POST /filters` - Create filter
- `PUT /filters/{id}` - Update filter
- `DELETE /filters/{id}` - Delete filter

#### Statistics
- `GET /stats` - System statistics
- `GET /stats/orders/daily` - Daily order stats
- `GET /stats/suppliers/performance` - Supplier performance

#### Activity
- `GET /activity` - Activity logs
- `GET /activity/recent` - Recent activity

Visit http://localhost:8000/docs for interactive API documentation.

## 🤖 Bot Commands

### Admin Commands
- `/start` - Main menu
- `/add_supplier` - Add new supplier
- `/create_order` - Create new order
- `/stats` - View statistics
- `/search_orders` - Search orders

### Supplier Commands
- `/start` - Register/Start
- `/my_orders` - View my orders
- `/profile` - View profile
- `/help` - Help information

## 🎯 Usage Examples

### Creating an Order
1. Admin sends `/start` and selects "Создать заказ"
2. Enters order text (can be multiple lines)
3. Bot creates order and assigns to suitable supplier
4. Supplier receives notification with inline buttons

### Managing Suppliers
1. Admin uses `/add_supplier`
2. Enters supplier name and keywords
3. System creates supplier with filters
4. Supplier can register with `/start`

### Viewing Statistics
1. Access dashboard at http://localhost:3000
2. Navigate to "Статистика" page
3. Select period (today, week, month, all)
4. View charts and metrics

## 🔒 Security Features

- JWT authentication for API
- Rate limiting with Nginx
- Input validation and sanitization
- SQL injection prevention with SQLAlchemy
- CORS configuration
- Security headers

## 🚀 Deployment

### Production Deployment

1. **Configure SSL certificates**
```bash
# Place certificates in nginx/ssl/
cp cert.pem nginx/ssl/
cp key.pem nginx/ssl/
```

2. **Update environment variables**
```bash
# Set production values
DEBUG=false
SECRET_KEY=your-very-secure-secret-key
```

3. **Enable HTTPS in nginx**
```bash
# Uncomment HTTPS server block in nginx/nginx.conf
```

4. **Deploy with Docker Compose**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Monitoring

- Health checks for all services
- Application logs
- Database metrics
- Redis performance monitoring

## 🛠️ Development

### Local Development Setup

1. **Install dependencies**
```bash
# Bot
pip install -r requirements.txt

# Dashboard
cd dashboard && npm install
```

2. **Start services locally**
```bash
# Database
docker-compose up -d db redis

# Bot
python -m bot.main

# API
uvicorn api.main:app --reload

# Dashboard
cd dashboard && npm start
```

### Code Quality

- Black for Python formatting
- ESLint for JavaScript
- Type hints throughout
- Comprehensive error handling

## 📈 Performance

- Redis caching for frequently accessed data
- Database connection pooling
- Lazy loading in React components
- Optimized database queries
- Gzip compression in Nginx

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Add tests
5. Submit pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/docs`

## 🔄 Updates

The system is designed to be:
- **Scalable** - Handle thousands of orders
- **Reliable** - 99.9% uptime target
- **Secure** - Enterprise-grade security
- **Maintainable** - Clean code architecture
- **Extensible** - Easy to add new features

---

**Built with ❤️ for efficient supply management**
