import { z } from "zod";

// User interface for MongoDB documents
export interface User {
  _id?: string;
  id?: string;
  username?: string;
  email?: string;
  password: string;
  role: string;
  created_at: Date;
  last_login?: Date;
  is_active: boolean;
}

// Validation schemas for user registration/login
export const insertUserSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters').optional(),
  email: z.string().email('Invalid email format').optional(),
  password: z.string().min(6, 'Password must be at least 6 characters'),
}).refine((data) => data.username || data.email, {
  message: "Either username or email is required",
  path: ["username"]
});

export const loginSchema = z.object({
  identifier: z.string().min(3, 'Username or email must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters')
});

export const registerSchema = z.object({
  identifier: z.string().min(3, 'Username or email must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string().min(6, 'Confirm password must be at least 6 characters')
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"]
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type LoginRequest = z.infer<typeof loginSchema>;
export type RegisterRequest = z.infer<typeof registerSchema>;

// Product interface for laptop products
export interface Product {
  ASIN: string;
  Model_Name: string;
  Release_Year: number;
  RAM_GB: number;
  Storage_GB: number;
  Color: string;
  Base_Price: number;
  image?: string;
}

// Static product data for demo
export const PRODUCTS: Product[] = [
  { 
    ASIN: 'B0B94152F6', 
    Model_Name: 'MacBook Air M2', 
    Release_Year: 2022, 
    RAM_GB: 8, 
    Storage_GB: 256, 
    Color: 'Midnight', 
    Base_Price: 110000 
  },
  { 
    ASIN: 'B0B94213G7', 
    Model_Name: 'MacBook Air M2', 
    Release_Year: 2022, 
    RAM_GB: 16, 
    Storage_GB: 512, 
    Color: 'Starlight', 
    Base_Price: 140000 
  },
  { 
    ASIN: 'B0CJ5KWD22', 
    Model_Name: 'MacBook Pro M3', 
    Release_Year: 2023, 
    RAM_GB: 8, 
    Storage_GB: 512, 
    Color: 'Space Grey', 
    Base_Price: 169900 
  },
  { 
    ASIN: 'B0CJ5LSM38', 
    Model_Name: 'MacBook Pro M3 Pro', 
    Release_Year: 2023, 
    RAM_GB: 18, 
    Storage_GB: 512, 
    Color: 'Space Black', 
    Base_Price: 199900 
  },
  { 
    ASIN: 'B08N5XSG8Z', 
    Model_Name: 'MacBook Air M1', 
    Release_Year: 2020, 
    RAM_GB: 8, 
    Storage_GB: 256, 
    Color: 'Silver', 
    Base_Price: 99900 
  },
];
