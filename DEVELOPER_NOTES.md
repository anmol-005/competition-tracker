Developer Notes — Competition Tracker / LabXpert
==============================================

Purpose
-------
This file documents the recent developer work (database integration, scraper fixes, frontend wiring, and authentication) and how to run/test the changes. It's meant as a short, practical reference for other devs joining the project.

High-level summary of work completed
------------------------------------

## Phase 1: MongoDB Atlas Integration & Product Display
- MongoDB Atlas integration
  - Added an async MongoDB service for the LabXpert server at `LabXpert/server/mongodb.ts` which connects to your provided Atlas cluster.
  - Service now transforms documents ONLY from `products` collection (catalog products) into the frontend's Product shape.
  - Removed mixing of scraping data with catalog products for clean product display.

- Backend API
  - Added product API endpoints in `LabXpert/server/routes.ts`:
    - `GET /api/products` → returns exactly 5 MacBook products from catalog (transformed to LabXpert format)
    - `GET /api/products/:asin` → returns single product by ASIN  
    - `GET /api/health` → simple health check
  - The routes file also initializes the MongoDB service on server start.

- Frontend integration (LabXpert / client)
  - **MAJOR FIX**: Replaced hard-coded product list completely in `client/src/pages/products.tsx` 
  - Frontend now shows ONLY database products (no hardcoded fallbacks)
  - Removed loading states and database indicators for seamless user experience
  - Built smart image-mapping for the 5 MacBook products with proper display names and prices
  - Added a React hook `client/src/hooks/use-products.ts` that uses `@tanstack/react-query` to fetch products

## Phase 2: Scraper Storage Fixes  
- **Fixed scraper data storage locations**:
  - Updated `scraper_db_utils.py` to store Amazon data in `amazon_scraping_data` collection
  - Updated to store Smartprix data in `smartprix_scraping_data` collection  
  - Updated to store Flipkart reviews in `flipkart_reviews` collection
  - Fixed all scrapers to use correct collections instead of mixing with `products` table

- **Enhanced scraper data extraction**:
  - Updated Amazon scraper CSS selectors for better rating/review extraction
  - Added multiple fallback selectors for Flipkart scraper to handle dynamic content
  - Improved data quality and extraction reliability

## Phase 3: Product Catalog Management
- **Database Product Storage**:
  - Created `store_macbook_products.py` to store 5 specific MacBook products with complete specifications
  - Products stored with proper field names, prices, RAM, storage, colors, and model names
  - All 5 MacBooks now display correctly: MacBook Air M2 Midnight (₹110,000), MacBook Air M2 Starlight (₹140,000), MacBook Pro M3 Space Grey (₹169,900), MacBook Pro M3 Pro Space Black (₹199,900), MacBook Air M1 Silver (₹99,900)

- **Clean API Response**:
  - API now returns exactly 5 products from database with correct data
  - Removed verbose logging for clean console output
  - Added debugging tools (`debug_products.py`, `test_labxpert_api.js`) for development

## Phase 4: Authentication System Enhancement
- **Database Schema Update**:
  - Updated user schema in `shared/schema.ts` to support both username and email registration
  - Users can now register/login with either username (e.g., "john123") or email (e.g., "john@example.com")

- **Backend Authentication**:
  - Enhanced `mongodb.ts` authentication methods to support username/email login
  - Updated API routes to accept `identifier` field for flexible authentication
  - Proper password hashing with bcrypt (12 rounds)
  - Session management with user data storage

- **Frontend Authentication**:
  - Updated `login.tsx` to support username/email in single field
  - Better user experience with unified login form
  - Clear validation messages and help text
  - Registration with username or email support

- **Admin Tools**:
  - Created `reset_admin_passwords.py` for admin password management
  - Default accounts: admin/admin123, analyst/analyst123, viewer/viewer123
  - Password reset utility for database maintenance

- Utilities & tests
  - `LabXpert/test-mongo.js` — quick Node script to test the LabXpert MongoDB service and print a sample of transformed products.
  - Created `.env.atlas` and `.env.local` templates in repo root to choose Atlas or local MongoDB.
  - Added helpful maintenance / setup scripts elsewhere (python-based) that were used to migrate sample data to Atlas (see `atlas_setup_test.py` and `enhanced_database_manager.py`).

Files added or changed (important)
---------------------------------

### LabXpert (Frontend/Backend):
- `LabXpert/server/mongodb.ts`  — MongoDB connection + user auth + product transformation (MAJOR UPDATE)
- `LabXpert/server/routes.ts`   — product API + authentication endpoints (login/register) 
- `LabXpert/shared/schema.ts`   — Updated user schema for username/email support
- `LabXpert/client/src/pages/login.tsx` — Enhanced authentication UI (username/email support)
- `LabXpert/client/src/pages/products.tsx` — Clean product display (database-only, no fallbacks)
- `LabXpert/client/src/hooks/use-products.ts` — React Query hooks for products
- `LabXpert/test_labxpert_api.js` — API testing script
- `LabXpert/package.json`      — MongoDB + bcrypt dependencies

### Python Scripts (Competition Tracker):
- `scraper_db_utils.py`        — Fixed storage locations for scrapers (CRITICAL FIX)
- `amazon_scraper.py`          — Updated CSS selectors for better data extraction  
- `flipkart_reviews.py`        — Enhanced selectors with multiple fallbacks
- `store_macbook_products.py`  — Product catalog management script
- `reset_admin_passwords.py`   — Admin password reset utility
- `debug_products.py`          — Database debugging tool
- `config.py`                  — Added new collection constants

### Configuration:
- `.env.example`, `.env.local`, `.env.atlas` — Environment templates
- `DEVELOPER_NOTES.md` (this file) — Updated with all recent changes

What to run and how to test (Windows / cmd.exe)
-----------------------------------------------
1) Install dependencies for LabXpert (if not done already)

```cmd
cd "d:\Programs Roshan\Infosys_project\competition-tracker\LabXpert"
npm install
```

2) Make sure your `.env` is set up
- Option A: Use Atlas (recommended for team)
  - Copy `.env.atlas` → `.env` and fill your Atlas credentials (username, password, cluster). Example (.env already provided earlier):

```text
MONGODB_USERNAME=myUser
MONGODB_PASSWORD=admin15
MONGODB_CLUSTER=competitiontrackerclust.o8dxgmq.mongodb.net
DATABASE_NAME=competition_tracker
```

- Option B: Local MongoDB
  - Copy `.env.local` → `.env`
  - Ensure `mongod` is running and accessible at `mongodb://localhost:27017/`

3) Start the dev server (if port 5000 is in use pick 5001)

```cmd
cd "d:\Programs Roshan\Infosys_project\competition-tracker\LabXpert"
set PORT=5001&& npm run dev
```

4) Verify API health and product list
- Health:

```cmd
curl http://localhost:5001/api/health
```

- Products (should return exactly 5 MacBooks):

```cmd
curl http://localhost:5001/api/products
```

You should see JSON with `success: true`, `count: 5`, and `products: []` (array of 5 MacBook products).

- Test API with Node script:

```cmd
node test_labxpert_api.js
```

5) Frontend Authentication & Products
- Open browser at the dev server address (usually `http://localhost:5001/`)  
- **Login Options**: You can now login with either username OR email:
  - Default accounts: `admin`/`admin123`, `analyst`/`analyst123`, `viewer`/`viewer123`
  - Or register new account with username (e.g., `john123`) or email (e.g., `john@example.com`)
- **Products Page**: Shows exactly 5 MacBook products from database with correct prices and specifications
- **No Loading States**: Clean, seamless experience with products loaded directly from database

Notes about images
------------------
- We only have five generated product images in `client/public/attached_assets/generated_images` used as high-quality thumbnails.
- The code maps database products' ASIN to these images where possible; otherwise a small heuristic picks an appropriate placeholder image by model & color.
- If you want every product to have its own image, upload images into `client/src/assets/generated_images` and map ASIN→filename in `client/src/pages/products.tsx`'s `productImages` mapping.

Authentication System (COMPLETED ✅)
------------------------------------

**FULL AUTHENTICATION IMPLEMENTED** - All requested features are now working:

### ✅ Completed Features:
- **Sign-in and Registration**: Full authentication system with username/email support
- **Default Admin Account**: Created with admin/admin123, analyst/analyst123, viewer/viewer123  
- **Database User Storage**: All users stored and validated from MongoDB users collection
- **Session Management**: Express sessions with secure cookie configuration
- **Password Security**: Bcrypt hashing with 12 rounds for all passwords

### 🔧 Authentication Endpoints:
- `POST /api/auth/register` — Create new user (username OR email + password)
- `POST /api/auth/login` — Login with username/email + password  
- `POST /api/auth/logout` — Destroy user session
- `GET /api/auth/me` — Get current authenticated user info

### 🎯 Key Features:
- **Flexible Registration**: Users can register with username (`john123`) OR email (`john@example.com`)
- **Unified Login**: Single login field accepts both username and email
- **Default Accounts**: admin, analyst, viewer accounts created automatically on server start
- **Password Reset**: `reset_admin_passwords.py` utility for admin password management
- **Session Security**: Secure cookie-based sessions with proper middleware

### 🔐 Default Login Credentials:
- **Admin**: `admin` / `admin123` (full access)
- **Analyst**: `analyst` / `analyst123` (data analysis role)  
- **Viewer**: `viewer` / `viewer123` (read-only access)

**Status**: ✅ AUTHENTICATION FULLY IMPLEMENTED AND WORKING

Notes about bcrypt
- The Python `passlib` warnings you saw earlier were due to a `passlib.handlers.bcrypt` problem in the Python scripts when trying to read the underlying `bcrypt` package version — this doesn't affect the Node backend.
- For the Node server we should install `bcrypt` (native) or `bcryptjs` (pure JS).
  - Recommended: `npm i bcrypt` (requires build tools) or `npm i bcryptjs` (no build tools). If Windows build issues happen, use `bcryptjs`.

Commands to add bcrypt (Node server)
-----------------------------------
From `LabXpert` directory, choose one:

```cmd
# Option A (native, recommended if your environment can build native modules)
npm install bcrypt

# Option B (pure JS fallback, easier in Windows)
npm install bcryptjs
```

Implementation notes for auth
-----------------------------
- Passwords MUST be stored hashed. Use `bcrypt.hash(password, 12)` on registration and `bcrypt.compare(password, hash)` on login.
- Use `express-session` + `memorystore` (already present in package.json) for server sessions, or issue signed JWT tokens and store them in the client.
- Protect `GET /api/products` if you want only authenticated users to see products (else keep public but prefer authenticated access for actions like add-to-cart, checkout).

Quick sketch of files to change when adding auth
-----------------------------------------------
- `LabXpert/server/mongodb.ts`  — add `insertUser`, `getUserByUsername` helpers
- `LabXpert/server/routes.ts`   — add auth routes (register/login/logout/me)
- `LabXpert/client/src/pages/login.tsx` — wire register & login forms to new endpoints (use `fetch` + `useQueryClient` or localStorage)
- `LabXpert/client/src/hooks`    — add `useAuth` hook and `AuthProvider` if you want global state

Database Collections & Data Flow
-------------------------------

### 📊 Current Collections:
- **`products`** — Catalog products (5 MacBooks) displayed on frontend
- **`amazon_scraping_data`** — Amazon scraping results (separate from catalog)
- **`smartprix_scraping_data`** — Smartprix scraping results (separate from catalog)  
- **`flipkart_reviews`** — Flipkart review data (separate from catalog)
- **`users`** — User accounts with username/email authentication

### 🔄 Data Flow:
1. **Scrapers** → Store data in respective scraping collections (amazon_scraping_data, etc.)
2. **Catalog Products** → Stored in `products` collection via `store_macbook_products.py`
3. **Frontend API** → Fetches ONLY from `products` collection (clean separation)
4. **User Authentication** → Uses `users` collection for login/registration

### 🎯 Key Design Decisions:
- **Separation of Concerns**: Scraping data kept separate from product catalog
- **Clean Frontend**: Only catalog products shown to users (no mixed scraping data)
- **Flexible Authentication**: Support for both username and email registration
- **Minimal Logging**: Clean console output in production


Maintenance & Troubleshooting
----------------------------

### 🔧 Common Tasks:
- **Reset Admin Passwords**: Run `python reset_admin_passwords.py` to reset default account passwords
- **Add New Products**: Update `store_macbook_products.py` and run to add catalog products
- **Test API**: Use `node test_labxpert_api.js` to verify API responses
- **Debug Database**: Run `python debug_products.py` to check database vs API consistency

### 🐛 Troubleshooting:
- **Port Conflicts**: Kill process using port 5000 or start on different port (`set PORT=5001&& npm run dev`)
- **MongoDB Atlas Issues**: Verify `.env` credentials and Atlas IP whitelist (or use 0.0.0.0/0 for dev)
- **Authentication Issues**: Check user exists in database, verify password with reset script
- **Product Display Issues**: Verify 5 products exist in database with `debug_products.py`
- **Build Failures**: For bcrypt issues, switch to `bcryptjs` in package.json

### 📱 API Testing:
```cmd
# Health check
curl http://localhost:5000/api/health

# Products (should return 5 MacBooks)  
curl http://localhost:5000/api/products

# User registration
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"identifier":"test@example.com","password":"test123","confirmPassword":"test123"}'

# User login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"test@example.com","password":"test123"}'
```

### 🎯 Current System Status:
- ✅ **Products**: 5 MacBooks displaying correctly from database
- ✅ **Authentication**: Username/email registration and login working  
- ✅ **Scrapers**: Storing data in correct collections (separate from catalog)
- ✅ **API**: Clean responses with proper transformation
- ✅ **Frontend**: Seamless user experience with database integration

— End of Developer Notes —
