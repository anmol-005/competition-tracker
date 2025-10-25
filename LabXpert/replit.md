# LapXpert - Project Documentation

## Overview

LapXpert is a modern, frontend-focused React.js e-commerce application showcasing premium MacBook laptops. The project emphasizes visual excellence, smooth user experience, and responsive design.

## Project Goal

Create a demo-ready laptop e-commerce store with:
- Simulated authentication flow
- Beautiful product showcase
- Responsive, mobile-friendly design
- Professional visual polish suitable for portfolio demonstrations

## Architecture

### Frontend Stack
- **React 18** with TypeScript for type safety
- **Wouter** for lightweight client-side routing
- **Tailwind CSS** for utility-first styling
- **shadcn/ui** for high-quality, accessible UI components
- **Vite** for fast development and optimized builds

### Key Design Decisions
1. **Frontend-Only Focus**: Authentication is simulated client-side for demo purposes
2. **Static Product Data**: 5 MacBook products defined in shared schema
3. **Component-Based Architecture**: Reusable ProductCard, Navbar, and layout components
4. **Theme Support**: Dark/light mode toggle with persistent localStorage state
5. **Responsive-First**: Mobile-first design approach with Tailwind breakpoints

## Page Structure

### `/login` - Authentication Page
- Email and password input fields
- Simulated authentication (accepts any credentials)
- Redirects to `/home` on successful login
- Stores auth state in localStorage

### `/home` - Product Showcase
- Hero section with workspace imagery and CTA
- Product grid displaying all 5 MacBooks
- Each product card shows: image, name, specs (RAM, storage, year, color), and price
- Non-functional "Add to Cart" buttons (UI only)

### `/cart` - Shopping Cart (Placeholder)
- Empty state with icon and message
- Navbar link initially disabled/greyed out
- Future enhancement target for cart functionality

## Component Architecture

### Core Components
- **ThemeProvider**: Manages light/dark mode state
- **ThemeToggle**: Sun/moon icon button for theme switching
- **Navbar**: Sticky navigation with logo, page links, logout, and theme toggle
- **ProductCard**: Reusable card component with image, specs grid, and CTA
- **ProtectedRoute**: HOC for authentication-guarded pages

### Design System
Following `design_guidelines.md`:
- **Colors**: Apple-inspired blue primary (#0080FF), clean grays for surfaces
- **Typography**: Inter font family, consistent size scale
- **Spacing**: Tailwind's 4/6/8/12 unit system
- **Components**: Shadcn Card, Button, Badge with hover-elevate utilities

## Data Model

```typescript
interface Product {
  ASIN: string;           // Amazon Standard Identification Number
  Model_Name: string;     // e.g., "MacBook Air M2"
  Release_Year: number;   // e.g., 2022
  RAM_GB: number;         // e.g., 8
  Storage_GB: number;     // e.g., 256
  Color: string;          // e.g., "Midnight"
  Base_Price: number;     // Price in INR (e.g., 110000)
}
```

## Recent Changes

### Initial Implementation (Current)
- Generated 6 AI product images (5 MacBooks + 1 hero image)
- Created complete schema with Product interface and static data
- Built all page components (Login, Home, Cart)
- Implemented Navbar with routing and theme toggle
- Designed ProductCard with specs grid and hover effects
- Added dark mode support with ThemeProvider
- Configured responsive breakpoints and Tailwind tokens

## User Preferences

- **Visual Quality Priority**: Frontend polish is paramount
- **Demo-Ready**: Clean, professional appearance for showcasing
- **Easy Deployment**: GitHub Pages and local Python server support
- **Learning-Friendly**: Well-commented code with logical structure

## Development Workflow

1. Start development server: `npm run dev`
2. Access at `http://localhost:5000`
3. Login with any credentials to access product showcase
4. Test responsive behavior across breakpoints
5. Verify dark/light mode toggle functionality

## Future Enhancements

Potential next phase features:
- Functional cart system with add/remove/quantity management
- Product filtering by price, RAM, storage, year
- Individual product detail pages
- Search functionality
- Persistent cart state
- Animation improvements

## Technical Notes

- **Authentication**: Purely client-side simulation - no backend validation
- **Images**: AI-generated MacBook product shots in attached_assets
- **Routing**: Protected routes check localStorage for auth state
- **State Management**: React Query for future API integration readiness
- **Build Output**: Vite bundles to `dist/public` for deployment

## Performance Considerations

- Lazy-loaded routes for code splitting
- Optimized images with proper aspect ratios
- Minimal bundle size with tree-shaking
- CSS purging via Tailwind for production builds
