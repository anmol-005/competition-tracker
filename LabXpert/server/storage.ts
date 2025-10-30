import { type User, type InsertUser } from "@shared/schema";
import { randomUUID } from "crypto";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;

  constructor() {
    this.users = new Map();
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    // Ensure all required fields from `User` are populated.
    // `insertUser` contains: password and either username or email.
    const user: User = {
      ...insertUser,
      id,
      // default role for newly created users
      role: 'user',
      // record creation time
      created_at: new Date(),
      // mark as active by default
      is_active: true,
    };

    this.users.set(id, user);
    return user;
  }
}

export const storage = new MemStorage();
