# E-commerce Shoe Store Design Guidelines

## Design Approach
**Reference-Based Approach** - Drawing inspiration from modern e-commerce leaders like Shopify and Nike for clean, product-focused design patterns that prioritize visual appeal and conversion.

## Core Design Elements

### Color Palette
- **Primary Brand**: 15 85% 25% (deep forest green for trust and premium feel)
- **Secondary**: 0 0% 95% (light gray for backgrounds)
- **Accent**: 25 95% 50% (vibrant orange for CTAs and highlights)
- **Text**: 220 15% 20% (dark blue-gray for readability)
- **Background**: 0 0% 99% (off-white for warmth)

### Typography
- **Primary Font**: Inter via Google Fonts CDN
- **Headings**: Font weights 600-700, sizes from text-xl to text-3xl
- **Body Text**: Font weight 400, sizes text-sm to text-base
- **Product Names**: Font weight 500, text-lg for prominence

### Layout System
**Tailwind Spacing Primitives**: Consistent use of units 2, 4, 6, 8, 12, and 16
- Buttons: px-6 py-3
- Cards: p-6 with gap-4
- Sections: py-12 with container max-width
- Grid gaps: gap-6 for product layouts

### Component Library

#### Navigation
- Clean navbar with subtle shadow (shadow-sm)
- Logo left-aligned, navigation center, user actions right
- Active state with border-b-2 in accent color
- Mobile hamburger menu for responsive design

#### Authentication
- Centered login form with max-w-md container
- Input fields with border-gray-300 and focus:ring-2 focus:ring-primary
- Primary button with full width and rounded-lg
- Subtle form validation styling

#### Product Cards
- Aspect-ratio-square image containers with object-cover
- White background with subtle shadow and rounded-xl corners
- Product name as heading, price prominently displayed
- "Add to Cart" button with primary color and hover states
- Consistent 4-column grid on desktop, 2-column on tablet, 1-column on mobile

#### Buttons
- Primary: Background in accent color with white text
- Secondary: Border style with primary color text
- Padding: px-6 py-3 for consistency
- Rounded-lg corners throughout
- Disabled state with opacity-50 for cart links

### Layout Structure

#### Login Page
- Full-height centered layout with subtle background pattern
- Card-based form with elevation
- Company branding at top
- Responsive form that works on all screen sizes

#### Homepage
- Hero section with brand messaging (optional minimal banner)
- Product grid section with clear hierarchy
- Footer with essential links
- Sticky navigation for easy access

### Responsive Design
- Mobile-first approach using Tailwind's responsive prefixes
- Breakpoints: sm: (640px), md: (768px), lg: (1024px)
- Grid adjustments: grid-cols-1 sm:grid-cols-2 lg:grid-cols-4
- Navigation collapses to hamburger menu on mobile

### Images
**Product Images**: High-quality shoe photography with consistent lighting and white/transparent backgrounds. Each product card needs a square aspect ratio image (400x400px minimum). Place images prominently at the top of each product card.

**No Hero Image**: This design focuses on immediate product discovery rather than lifestyle imagery, keeping the homepage clean and conversion-focused.

### Interactive States
- Hover effects on product cards with subtle scale transform
- Button hover states with slight color darkening
- Focus states for form inputs with ring styling
- Loading states for simulated login process

This design prioritizes clean product presentation, easy navigation, and professional aesthetics suitable for demo presentation while maintaining the familiar e-commerce patterns users expect.