# 🖥️ Complete Setup Guide for Competition Tracker

## 📋 **Prerequisites**

Before setting up the project, ensure you have these installed on your laptop:

### **Required Software:**
- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/en/download/)
- **Git** - [Download from git-scm.com](https://git-scm.com/downloads/)
- **Google AI API Key** - [Get from Google AI Studio](https://makersuite.google.com/app/apikey)

### **Optional (for custom database):**
- **MongoDB Atlas Account** - [Free at mongodb.com](https://www.mongodb.com/atlas)

---

## 🚀 **Step-by-Step Setup**

### **Step 1: Clone the Repository**

```bash
# Clone the project
git clone https://github.com/anmol-005/competition-tracker.git

# Navigate to project directory
cd competition-tracker
```

### **Step 2: Python Environment Setup**

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate

# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
python -m playwright install chromium
```

### **Step 3: Environment Configuration**

```bash
# Copy environment template to working file
cp .env.example .env

# Edit .env file with your credentials
# Use any text editor (notepad, VS Code, etc.)
```

**Required Environment Variables in `.env`:**

```bash
# Google AI Configuration (REQUIRED)
API=your_google_ai_api_key_here

# MongoDB Configuration (Use existing shared database)
MONGODB_USERNAME=myUser
MONGODB_PASSWORD=admin15
MONGODB_CLUSTER=competitiontrackerclust.o8dxgmq.mongodb.net
DATABASE_NAME=competition_tracker
MONGODB_URL=

# Or use your own MongoDB Atlas
# MONGODB_USERNAME=your_username
# MONGODB_PASSWORD=your_password
# MONGODB_CLUSTER=your-cluster.xxxxx.mongodb.net

# Security (generate a strong secret key)
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-32-chars-min
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
```

### **Step 4: LabXpert Frontend Setup**

```bash
# Navigate to LabXpert directory
cd LabXpert

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

### **Step 5: Test the Setup**

**Test Python Components:**
```bash
# Return to root directory
cd ..

# Test MongoDB connection
python -c "from config import config; print('✅ Config loaded:', config.DATABASE_NAME)"

# Test AI-powered price prediction
python llm.py

# Test individual scrapers
python amazon_scraper.py
python flipkart_scraper.py
python smartprix_scraper.py
```

**Test Web Application:**
```bash
# Access the web app
# Open browser: http://localhost:5000

# Login with default credentials:
# Username: admin | Password: admin123
# Username: analyst | Password: analyst123
# Username: viewer | Password: viewer123
```

---

## 🎯 **Quick Start Commands**

### **For Python Scripts Only:**
```bash
git clone https://github.com/anmol-005/competition-tracker.git
cd competition-tracker
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
# Edit .env with your Google AI API key
python llm.py
```

### **For Full Web Application:**
```bash
git clone https://github.com/anmol-005/competition-tracker.git
cd competition-tracker
cp .env.example .env
# Edit .env with your API key
cd LabXpert
npm install
npm run dev
# Open http://localhost:5000
```

---

## 🔧 **Configuration Details**

### **Google AI API Key Setup:**
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create new API key
4. Copy the key and paste in `.env` file:
   ```bash
   API=AIza...your_actual_key_here
   ```

### **MongoDB Connection Options:**

#### **Option A: Use Shared Database (Easiest)**
```bash
# In .env file, use these existing credentials:
MONGODB_USERNAME=myUser
MONGODB_PASSWORD=admin15
MONGODB_CLUSTER=competitiontrackerclust.o8dxgmq.mongodb.net
```

#### **Option B: Create Your Own Database**
1. Go to https://www.mongodb.com/atlas
2. Create free account and cluster
3. Create database user
4. Get connection details
5. Update `.env` with your credentials

#### **Option C: Local MongoDB (Advanced)**
```bash
# Install MongoDB Community Server locally
# Update .env:
MONGODB_URL=mongodb://localhost:27017/competition_tracker
MONGODB_USERNAME=
MONGODB_PASSWORD=
MONGODB_CLUSTER=
```

---

## 🖥️ **Platform-Specific Notes**

### **Windows Users:**
```cmd
# Use Command Prompt or PowerShell
# Virtual environment activation:
venv\\Scripts\\activate

# If execution policy issues in PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **macOS Users:**
```bash
# Virtual environment activation:
source venv/bin/activate

# If Python 3 is not default:
python3 -m venv venv
pip3 install -r requirements.txt
```

### **Linux Users:**
```bash
# Install Python development tools if needed:
sudo apt update
sudo apt install python3-pip python3-venv python3-dev

# Continue with standard setup
python3 -m venv venv
source venv/bin/activate
```

---

## 🔍 **Troubleshooting Common Issues**

### **Python Import Errors:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies:
pip install --force-reinstall -r requirements.txt
```

### **Playwright Browser Issues:**
```bash
# Reinstall browsers:
python -m playwright install --force
```

### **Node.js Module Issues:**
```bash
# Clear npm cache and reinstall:
cd LabXpert
rm -rf node_modules package-lock.json  # or del on Windows
npm install
```

### **MongoDB Connection Issues:**
```bash
# Test connection with Python:
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient('your_connection_string_here')
    try:
        await client.admin.command('ping')
        print('✅ MongoDB Connected')
    except Exception as e:
        print(f'❌ MongoDB Error: {e}')

asyncio.run(test())
"
```

### **Google AI API Issues:**
```bash
# Test API key:
python -c "
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('API'))

try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    print('✅ Google AI Connected')
except Exception as e:
    print(f'❌ Google AI Error: {e}')
"
```

---

## 📱 **Usage Examples**

### **Run AI Price Prediction:**
```bash
python llm.py
# Output: Cross-platform price analysis with AI recommendations
```

### **Run Individual Scrapers:**
```bash
# Amazon scraping
python amazon_scraper.py

# Flipkart scraping  
python flipkart_scraper.py

# Smartprix scraping
python smartprix_scraper.py
```

### **Access Web Application:**
```bash
# Start LabXpert
cd LabXpert
npm run dev

# Open http://localhost:5000
# Login: admin / admin123
# Browse products, view analytics, manage data
```

---

## 🎉 **Success Indicators**

You've successfully set up the project when you can:

- ✅ **Python Scripts**: Run `python llm.py` and see AI price recommendations
- ✅ **Web App**: Access http://localhost:5000 and login successfully  
- ✅ **Database**: See products loaded from MongoDB
- ✅ **Scrapers**: Run scrapers without errors
- ✅ **AI Integration**: Get intelligent price predictions

---

## 🆘 **Getting Help**

If you encounter issues:

1. **Check Requirements**: Ensure all prerequisites are installed
2. **Verify Environment**: Double-check `.env` file configuration
3. **Check Logs**: Look for error messages in terminal output
4. **Test Components**: Run individual components to isolate issues
5. **Check Network**: Ensure internet connection for API/database access

## 📞 **Contact & Support**

- **GitHub Issues**: [Report bugs](https://github.com/anmol-005/competition-tracker/issues)
- **Documentation**: Check README.md for additional details
- **Environment Guide**: See ENVIRONMENT_SETUP.md for configuration help

---

**🎯 That's it! You now have a fully functional competition tracker with AI-powered price predictions running on your laptop.**