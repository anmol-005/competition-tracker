# 🛒 Competition Tracker - E-commerce Intelligence Platform

**Project Status: Production Ready**

A comprehensive competitive intelligence tool for e-commerce businesses featuring AI-powered price predictions, multi-platform scraping, and a modern React frontend. The system monitors competitor pricing across Amazon, Flipkart, and Smartprix, uses Google AI for intelligent price recommendations, and includes a full-featured web application with authentication and product management.

---

## 🚀 Features

### 🤖 AI-Powered Price Intelligence
- **Smart Price Predictions**: Google Gemini AI analyzes cross-platform data to recommend optimal pricing strategies
- **Multi-Platform Scraping**: Automated data collection from Amazon, Flipkart, and Smartprix
- **Specification Matching**: Advanced algorithm matches products across platforms using storage, brand, model, and color
- **Real-time Analysis**: Live price monitoring with MongoDB Atlas storage

### 🎨 Modern Web Application (LabXpert)
- **Authentication System**: Secure login/registration with role-based access (Admin, Analyst, Viewer)
- **Product Showcase**: Premium MacBook catalog with responsive design
- **Dark/Light Mode**: Complete theme switching with modern UI components
- **Real-time Data**: Frontend connects to scraped product database

### 📊 Data Management
- **MongoDB Integration**: Cloud-based storage with automatic data synchronization
- **Cross-Platform Matching**: Intelligent product identification across multiple e-commerce sites
- **Price History**: Track pricing trends and competitor strategies
- **Export Capabilities**: Data export for further analysis

## 👨‍💻 Team: Cognitive Crew

| Member Name | Role | Contributions |
| :--- | :--- | :--- |
| **Dinesh** (Team Lead) | Frontend Architecture | React.js, UI/UX Design |
| **Anmol Kansal** (Assistant Lead) | Backend & AI Integration | Python, Google AI, API Development |
| **Ankita Barui** | Data Engineering | Python, Web Scraping, Data Processing |
| **Roshan Vishwakarma** | Database Architecture | MongoDB, Data Storage, Schema Design |
| **Sharanya** | Full-Stack & Design | Python, FastAPI, UI/UX |

---

## 🏗️ Project Architecture

```
competition-tracker/
├── 🤖 AI & Scraping Components
│   ├── llm.py                    # Google AI price prediction engine
│   ├── amazon_scraper.py         # Amazon data extraction
│   ├── flipkart_scraper.py       # Flipkart data extraction
│   ├── smartprix_scraper.py      # Smartprix data extraction
│   ├── scraper_db_utils.py       # Database utilities
│   └── config.py                 # MongoDB configuration
│
└── 🎨 LabXpert Web Application
    ├── client/                   # React.js frontend
    │   ├── src/
    │   │   ├── components/       # UI components
    │   │   ├── pages/           # Application pages
    │   │   └── hooks/           # Custom React hooks
    ├── server/                   # Express.js backend
    │   ├── routes.ts            # API endpoints
    │   ├── mongodb.ts           # Database service
    │   └── storage.ts           # User management
    └── shared/                   # TypeScript schemas
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **MongoDB Atlas Account** (free tier available)
- **Google AI API Key** (Gemini models)

### 1. Clone & Setup Repository
```bash
git clone https://github.com/anmol-005/competition-tracker.git
cd competition-tracker
```

### 2. Python Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers for scraping
python -m playwright install chromium
```

### 3. Environment Configuration
Create environment files with your credentials:

```bash
# Root directory - create .env
API=your_google_ai_api_key_here
MONGODB_URL=your_mongodb_atlas_connection_string
```

### 4. LabXpert Frontend Setup
```bash
cd LabXpert

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

### 5. Run the AI Price Prediction System
```bash
# Return to root directory
cd ..

# Run the LLM price prediction
python llm.py

# Or run individual scrapers
python amazon_scraper.py
python flipkart_scraper.py
python smartprix_scraper.py
```

## 🔧 Configuration Guide

### MongoDB Atlas Setup
1. Create a free MongoDB Atlas account at https://www.mongodb.com/atlas
2. Create a new cluster (free tier M0 available)
3. Add your IP address to the whitelist
4. Create a database user with read/write permissions
5. Get your connection string and add it to `.env`

### Google AI API Setup
1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key for Gemini models
3. Add the API key to your `.env` file
4. Ensure billing is enabled for higher rate limits

### Default Login Credentials
- **Admin**: `admin` / `admin123`
- **Analyst**: `analyst` / `analyst123`
- **Viewer**: `dataview` / `dataview123`

## 📖 Usage Guide

### Running Price Analysis
```bash
# Complete cross-platform price analysis with AI recommendations
python llm.py
```
**Output Example:**
```
🔵 2-Platform Product #1
Product: Apple iPhone 15 (128 GB) - Black
Amazon: ₹51,990 | Rating: 4.5
Flipkart: ₹59,900 | Rating: 4.6

🤖 AI Price Recommendation:
Recommended Price: ₹54,990
This price balances profitability with competitiveness, positioned below 
the average market price while maintaining healthy profit margins.
```

### Web Application Features
1. **Access**: Navigate to `http://localhost:5000` after running `npm run dev`
2. **Login**: Use default credentials or register new accounts
3. **Products**: Browse scraped products with real-time pricing data
4. **Authentication**: Role-based access with Admin/Analyst/Viewer permissions

### Individual Scraper Usage
```bash
# Amazon scraper with search term
python amazon_scraper.py

# Flipkart scraper
python flipkart_scraper.py

# Smartprix scraper
python smartprix_scraper.py
```

## 🔌 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Product Endpoints
- `GET /api/products` - Fetch all products from database
- `GET /api/products/:asin` - Get single product by ASIN
- `GET /api/health` - API health check

### Admin Endpoints
- `GET /api/admin/users` - Get all users (admin only)

## 🛠️ Development

### Frontend Development
```bash
cd LabXpert

# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Type checking
npm run check
```

### Backend API Development
```bash
cd LabXpert

# Start backend server
npm run dev

# The API will be available at http://localhost:5000/api
```

### Database Operations
The system automatically:
- Creates MongoDB collections for each platform
- Handles data synchronization across platforms
- Manages user authentication and sessions
- Stores product data with automatic deduplication

## 🚀 Deployment

### Production Build
```bash
cd LabXpert
npm run build
npm start
```

### Environment Variables for Production
```bash
NODE_ENV=production
PORT=5000
MONGODB_URL=your_production_mongodb_url
API=your_google_ai_api_key
```

## 🧪 Testing

### Run TypeScript Checks
```bash
cd LabXpert
npm run check
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Get products
curl http://localhost:5000/api/products
```

## 📊 Monitoring & Analytics

The system provides comprehensive insights:
- **Cross-platform price comparison**
- **AI-powered pricing recommendations**
- **Product specification matching**
- **Real-time competitor monitoring**
- **Historical price trends**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google AI**: Gemini models for intelligent price predictions
- **MongoDB Atlas**: Cloud database platform
- **crawl4ai**: Web scraping capabilities
- **React.js & TypeScript**: Modern frontend development
- **Tailwind CSS**: Utility-first CSS framework
