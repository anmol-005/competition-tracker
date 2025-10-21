# LabXpert - Store

## Overview
LabXpert - Store is a modern e-commerce platform specializing in premium sneakers and shoes from top brands like Nike, Adidas, Jordan, Converse, and Vans. The application features a clean, product-focused design with user authentication, product browsing, and shopping cart functionality. Built as a full-stack web application with a React frontend and Express backend, it emphasizes visual appeal and conversion optimization through modern UI patterns.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript using Vite as the build tool
- **Routing**: Wouter for client-side routing with protected routes for authenticated users
- **UI Framework**: shadcn/ui component library built on Radix UI primitives
- **Styling**: Tailwind CSS with custom design system following e-commerce best practices
- **State Management**: React hooks for local state management with TanStack Query for server state
- **Design System**: Custom color palette with deep forest green primary, vibrant orange accents, and consistent spacing using Tailwind primitives

### Backend Architecture
- **Framework**: Express.js with TypeScript
- **API Structure**: RESTful API with all routes prefixed under `/api`
- **Storage Layer**: Abstract storage interface (`IStorage`) with in-memory implementation for development
- **Session Management**: Express sessions with PostgreSQL session store (connect-pg-simple)
- **Development Tools**: Hot module replacement via Vite integration in development mode

### Authentication & Authorization
- **Authentication Flow**: Form-based login with username/password credentials
- **Route Protection**: Client-side route guards that redirect unauthenticated users to login
- **Session Storage**: Server-side sessions with secure cookie management
- **User Model**: Simple user schema with username, password, and UUID primary keys

### Data Layer
- **ORM**: Drizzle ORM with PostgreSQL dialect for type-safe database operations
- **Database**: PostgreSQL with Neon serverless database provider
- **Schema Management**: Code-first approach with Drizzle migrations
- **Validation**: Zod schemas for runtime type validation and API contract enforcement

### Component Architecture
- **Design Pattern**: Composition-based components with consistent prop interfaces
- **Product Display**: Reusable ProductCard and ProductGrid components for scalable catalog presentation
