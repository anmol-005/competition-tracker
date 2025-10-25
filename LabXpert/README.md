# LapXpert - Premium MacBook E-Commerce Frontend

A modern, human-friendly React.js laptop e-commerce store showcasing premium MacBook products with a clean, professional design.

## Features

- **Authentication**: Dedicated login page with simulated authentication
- **Product Showcase**: Beautiful product grid displaying 5 MacBook models
- **Responsive Design**: Mobile-first design that looks great on all devices
- **Dark Mode**: Toggle between light and dark themes
- **Modern UI**: Built with Tailwind CSS and shadcn/ui components
- **Smooth Interactions**: Hover effects, transitions, and polished user experience

## Technology Stack

- **Frontend**: React.js with TypeScript
- **Routing**: Wouter (lightweight React router)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Build Tool**: Vite
- **Backend**: Express.js (minimal server for hosting)

## Getting Started

### Prerequisites

- Node.js 20 or higher
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lapxpert
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:5000`

### Default Login

Enter any email and password to login - authentication is simulated for demo purposes.

## Project Structure

```
lapxpert/
├── client/                 # Frontend React application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components (Login, Home, Cart)
│   │   ├── lib/           # Utility functions
│   │   └── App.tsx        # Main app component with routing
│   └── index.html         # HTML entry point
├── server/                # Backend Express server
├── shared/                # Shared types and schemas
└── attached_assets/       # Generated product images

```

## Product Data

The application displays 5 MacBook models with the following information:
- MacBook Air M2 (Midnight, 8GB/256GB) - ₹110,000
- MacBook Air M2 (Starlight, 16GB/512GB) - ₹140,000
- MacBook Pro M3 (Space Grey, 8GB/512GB) - ₹169,900
- MacBook Pro M3 Pro (Space Black, 18GB/512GB) - ₹199,900
- MacBook Air M1 (Silver, 8GB/256GB) - ₹99,900

## Deployment

### GitHub Pages

1. Build the project:
```bash
npm run build
```

2. The built files will be in the `dist/public` directory

3. Deploy to GitHub Pages using your preferred method

### Local Python Server

For quick local testing with a simple HTTP server:

```bash
python3 main.py
```

This will serve the built application on `http://localhost:8000`

## Features Roadmap

Future enhancements could include:
- Functional shopping cart with add/remove items
- Product filtering and sorting
- Detailed product pages
- Search functionality
- Persistent cart state with localStorage
- User accounts and order history

## Design Philosophy

LapXpert follows modern e-commerce design principles:
- **Product-first**: Clean layouts that showcase MacBooks beautifully
- **Premium feel**: Visual design that reflects product quality
- **Effortless navigation**: Intuitive user flow
- **Trust signals**: Professional presentation builds confidence

## License

MIT License - feel free to use this project for learning and demonstration purposes.

## Credits

Built with modern web technologies and best practices. Product images generated using AI for demonstration purposes.
