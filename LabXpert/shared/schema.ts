import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User schema for authentication
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

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
