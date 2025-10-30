import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { mongoService } from "./mongodb";
import bcrypt from "bcrypt";
import session from "express-session";
import { z } from "zod";

// Extend session type to include user
declare module 'express-session' {
  interface SessionData {
    user?: {
      id: string;
      username: string;
      email?: string;
      role: string;
    };
  }
}

export async function registerRoutes(app: Express): Promise<Server> {
  // Session configuration
  app.use(session({
    secret: 'labxpert_secret_key_2024', // In production, use environment variable
    resave: false,
    saveUninitialized: false,
    cookie: { 
      secure: false, // Set to true in production with HTTPS
      httpOnly: true,
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
  }));

  // Initialize MongoDB connection and create default admin
  try {
    await mongoService.connect();
    await mongoService.createDefaultAdmin(); // Create default admin account
    console.log('🗄️ MongoDB service initialized for LabXpert');
  } catch (error) {
    console.error('❌ Failed to initialize MongoDB service:', error);
  }
  
  // API Routes - prefix all routes with /api
  
  // Get all products from database
  app.get("/api/products", async (req, res) => {
    try {
      console.log('📦 Fetching products from database...');
      const products = await mongoService.getProducts();
      
      res.json({
        success: true,
        count: products.length,
        products: products
      });
      
      console.log(`✅ Sent ${products.length} products to frontend`);
    } catch (error) {
      console.error('❌ Error fetching products:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch products from database',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Get single product by ASIN
  app.get("/api/products/:asin", async (req, res) => {
    try {
      const { asin } = req.params;
      const products = await mongoService.getProducts();
      const product = products.find(p => p.ASIN === asin);
      
      if (!product) {
        return res.status(404).json({
          success: false,
          error: 'Product not found'
        });
      }
      
      res.json({
        success: true,
        product: product
      });
    } catch (error) {
      console.error('❌ Error fetching product:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch product from database'
      });
    }
  });

  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({
      success: true,
      message: "LabXpert API is running",
      timestamp: new Date().toISOString(),
      database: "MongoDB Atlas Connected"
    });
  });

  // ===== AUTHENTICATION ENDPOINTS =====

  // Import validation schemas from shared schema
  const { loginSchema, registerSchema } = await import('../shared/schema.js');

  // Middleware to check if user is authenticated
  const requireAuth = (req: any, res: any, next: any) => {
    if (!req.session?.user) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required'
      });
    }
    next();
  };

  // Middleware to check if user is admin
  const requireAdmin = (req: any, res: any, next: any) => {
    if (!req.session?.user || req.session.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        error: 'Admin access required'
      });
    }
    next();
  };

  // User registration
  app.post("/api/auth/register", async (req, res) => {
    try {
      const validation = registerSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({
          success: false,
          error: 'Validation failed',
          details: validation.error.issues
        });
      }

      const { identifier, password } = validation.data;

      // Create new user
      const newUser = await mongoService.createUser(identifier, password, 'user');
      
      res.status(201).json({
        success: true,
        message: 'User registered successfully',
        user: {
          id: newUser.id,
          username: newUser.username,
          email: newUser.email,
          role: newUser.role
        }
      });

    } catch (error: any) {
      console.error('❌ Registration error:', error);
      
      if (error.message === 'Username already exists') {
        return res.status(409).json({
          success: false,
          error: 'Username already exists'
        });
      }
      
      res.status(500).json({
        success: false,
        error: 'Registration failed',
        message: error.message
      });
    }
  });

  // User login
  app.post("/api/auth/login", async (req, res) => {
    try {
      const validation = loginSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({
          success: false,
          error: 'Validation failed',
          details: validation.error.issues
        });
      }

      const { identifier, password } = validation.data;

      // Authenticate user
      const user = await mongoService.authenticateUser(identifier, password);
      
      if (!user) {
        return res.status(401).json({
          success: false,
          error: 'Invalid username/email or password'
        });
      }

      // Store user in session
      req.session.user = {
        id: user.id.toString(),
        username: user.username || user.email || 'unknown',
        role: user.role
      };

      res.json({
        success: true,
        message: 'Login successful',
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role
        }
      });

    } catch (error: any) {
      console.error('❌ Login error:', error);
      res.status(500).json({
        success: false,
        error: 'Login failed',
        message: error.message
      });
    }
  });

  // User logout
  app.post("/api/auth/logout", (req, res) => {
    req.session.destroy((err) => {
      if (err) {
        console.error('❌ Logout error:', err);
        return res.status(500).json({
          success: false,
          error: 'Logout failed'
        });
      }
      
      res.clearCookie('connect.sid');
      res.json({
        success: true,
        message: 'Logout successful'
      });
    });
  });

  // Get current user
  app.get("/api/auth/me", requireAuth, (req, res) => {
    res.json({
      success: true,
      user: req.session.user
    });
  });

  // Get all users (admin only)
  app.get("/api/admin/users", requireAdmin, async (req, res) => {
    try {
      const users = await mongoService.getAllUsers();
      res.json({
        success: true,
        users: users
      });
    } catch (error: any) {
      console.error('❌ Error fetching users:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch users',
        message: error.message
      });
    }
  });

  // use storage to perform CRUD operations on the storage interface
  // e.g. storage.insertUser(user) or storage.getUserByUsername(username)

  const httpServer = createServer(app);

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('🔄 Shutting down server...');
    await mongoService.disconnect();
    process.exit(0);
  });

  return httpServer;
}
