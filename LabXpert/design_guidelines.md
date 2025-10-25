# LapXpert Design Guidelines

## Design Approach: Reference-Based (Apple.com + Modern E-commerce)

**Inspiration Sources**: Apple.com's product-focused minimalism, Shopify's clean commerce patterns, with modern card-based layouts for product discovery.

**Core Principles**:
- Product-first: Let MacBook imagery and specs shine
- Premium feel: Reflect the quality of products being sold
- Effortless navigation: Intuitive flow from login → browse → cart
- Trust signals: Professional presentation builds purchase confidence

---

## Color Palette

**Light Mode**:
- Background: 0 0% 98% (near-white, clean canvas)
- Surface: 0 0% 100% (pure white cards)
- Primary: 210 100% 50% (Apple-inspired blue for CTAs)
- Text Primary: 0 0% 13% (deep charcoal)
- Text Secondary: 0 0% 45% (medium gray for specs)
- Border: 0 0% 90% (subtle card borders)

**Dark Mode**:
- Background: 0 0% 7% (rich black)
- Surface: 0 0% 12% (elevated card surface)
- Primary: 210 100% 60% (brighter blue for dark)
- Text Primary: 0 0% 95% (off-white)
- Text Secondary: 0 0% 65% (lighter gray)
- Border: 0 0% 20% (subtle separation)

**Accent**: Use sparingly for success states (e.g., "Added to Cart" feedback) - 142 76% 45% (green)

---

## Typography

**Font Family**: 
- Primary: 'Inter' (Google Fonts) - clean, modern sans-serif
- Monospace: 'SF Mono' or 'Roboto Mono' for ASIN codes

**Scale**:
- Hero/Brand: text-4xl to text-5xl, font-bold
- Product Names: text-xl, font-semibold
- Body/Specs: text-base, font-normal
- Labels: text-sm, font-medium
- Price: text-2xl, font-bold (standout element)

---

## Layout System

**Spacing Primitives**: Use Tailwind units of 2, 4, 6, 8, 12, 16 for consistency
- Component padding: p-4, p-6, p-8
- Section margins: mb-8, mb-12, mb-16
- Grid gaps: gap-6, gap-8

**Container Strategy**:
- Max-width: max-w-7xl (1280px) for main content
- Padding: px-4 (mobile), px-6 (tablet), px-8 (desktop)

**Grid Layouts**:
- Product Grid: grid-cols-1 (mobile), md:grid-cols-2 (tablet), lg:grid-cols-3 (desktop)
- 5 products displayed: 3 columns on large screens creates balanced layout

---

## Component Library

### Navigation Bar
- Fixed top position with backdrop blur
- Height: h-16
- Logo left, nav links center, user actions right
- Cart link initially greyed out (opacity-40) with tooltip "Add items to enable"
- Smooth hover states on links (hover:text-primary transition)

### Login Page
- Centered card (max-w-md) on gradient background
- Subtle shadow (shadow-xl) for depth
- Input fields: rounded-lg, p-3, focus:ring-2 ring-primary
- Single "Login" button: full-width, bg-primary, hover:brightness-110

### Product Cards
- White/surface background with rounded-xl borders
- Hover effect: scale-105 transition with shadow-2xl
- Product image: aspect-video or 4:3 ratio, object-cover
- Specs grid: 2-column layout (RAM/Storage, Year/Color)
- Price: prominently displayed at bottom in larger text
- "Add to Cart" button: w-full, primary color, rounded-lg

### Branding
- "LapXpert" logo in navbar: text-2xl, font-bold with subtle gradient or icon
- Tagline optional: "Premium MacBooks, Expert Choice"

---

## Visual Enhancements

**Product Card Details**:
- Hover: Lift effect (transform translate-y-1) + enhanced shadow
- Image overlay: Subtle gradient on hover to highlight "Add to Cart"
- Spec badges: Small rounded pills (bg-gray-100 dark:bg-gray-800) for quick scanning

**Decorative Elements**:
- Subtle gradient backgrounds (light: blue-50 to purple-50, dark: subtle radial)
- Icons from Heroicons for specs (CPU icon for RAM, hard drive for storage, etc.)
- Micro-animations: Fade-in on page load, button press feedback

**Trust Signals**:
- Display "Official Apple Authorized Reseller" badge (if applicable)
- Product authenticity indicators (verified checkmarks)

---

## Images

**Hero Section**: Yes - Include a prominent hero
- Full-width hero banner showcasing latest MacBook with lifestyle imagery
- Height: 60vh on desktop, 40vh on mobile
- Overlay text: "Welcome to LapXpert" + tagline
- CTA: "Browse Collection" button with blurred background (backdrop-blur-sm bg-white/20)

**Product Cards**: 
- High-quality MacBook product shots (front-facing, clean white/black backgrounds)
- Consistent aspect ratio across all cards
- Use placeholder images from Unsplash/Pexels for MacBooks or solid color placeholders with model names

**Image Sources**:
- Hero: MacBook on desk in modern workspace (Unsplash search: "macbook workspace")
- Products: Individual MacBook models (search by color: Silver, Space Gray, Midnight, Starlight, Space Black)
- Fallback: Use gradient placeholders with model name if images unavailable

---

## Responsive Behavior

**Breakpoints**:
- Mobile (<768px): Single column, stacked navigation
- Tablet (768-1024px): 2-column product grid
- Desktop (>1024px): 3-column grid, full navbar

**Mobile Optimizations**:
- Hamburger menu for navigation
- Larger touch targets (min-h-12 for buttons)
- Reduced padding on cards (p-4 instead of p-6)

---

## Animations

Use sparingly for polish:
- Page transitions: Fade-in (opacity 0→1, duration-300)
- Card hover: Transform + shadow (transition-all duration-200)
- Button states: Brightness/scale on click (active:scale-95)
- NO scroll-triggered animations or complex motion

---

## Accessibility

- Maintain WCAG AA contrast ratios (4.5:1 for text)
- Focus rings on all interactive elements (ring-2 ring-primary)
- Alt text for all product images
- Keyboard navigation support (tab order logical)
- Disabled cart link includes aria-label explanation