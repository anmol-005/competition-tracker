import { Link, useLocation } from "wouter";
import { ShoppingCart, LogOut, Home, Footprints } from "lucide-react";
import { Button } from "@/components/ui/button";

interface NavbarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
  cartItemCount?: number;
}

export default function Navbar({ isLoggedIn, onLogout, cartItemCount = 0 }: NavbarProps) {
  const [location] = useLocation();

  if (!isLoggedIn) return null;

  return (
    <nav className="bg-background border-b shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/home" data-testid="link-logo">
            <div className="flex items-center gap-2 hover-elevate rounded-lg px-3 py-2">
              <Footprints className="w-6 h-6 text-primary" />
              <span className="text-xl font-bold text-foreground">SoleStyle</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-2">
            <Link href="/home" data-testid="link-home">
              <Button 
                variant={location === "/home" ? "default" : "ghost"} 
                size="sm"
                className="gap-2 font-medium"
              >
                <Home className="w-4 h-4" />
                Home
              </Button>
            </Link>
            <Link href="/shoes" data-testid="link-shoes">
              <Button 
                variant={location === "/shoes" ? "default" : "ghost"} 
                size="sm"
                className="gap-2 font-medium"
              >
                <Footprints className="w-4 h-4" />
                Shoes
              </Button>
            </Link>
            <Link href="/cart" data-testid="link-cart">
              <Button 
                variant={location === "/cart" ? "default" : "ghost"} 
                size="sm"
                className="gap-2 font-medium"
              >
                <ShoppingCart className="w-4 h-4" />
                Cart {cartItemCount > 0 && `(${cartItemCount})`}
              </Button>
            </Link>
          </div>

          {/* User Actions */}
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onLogout}
              className="gap-2 font-medium"
              data-testid="button-logout"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden pb-4">
          <div className="flex items-center justify-around">
            <Link href="/home" data-testid="link-home-mobile">
              <Button 
                variant={location === "/home" ? "default" : "ghost"} 
                size="sm"
                className="gap-2 font-medium"
              >
                <Home className="w-4 h-4" />
                Home
              </Button>
            </Link>
            <Link href="/shoes" data-testid="link-shoes-mobile">
              <Button 
                variant={location === "/shoes" ? "default" : "ghost"} 
                size="sm"
                className="gap-2 font-medium"
              >
                <Footprints className="w-4 h-4" />
                Shoes
              </Button>
            </Link>
            <Link href="/cart" data-testid="link-cart-mobile">
              <Button 
                variant={location === "/cart" ? "default" : "ghost"} 
                size="sm"
                className="gap-2 font-medium"
              >
                <ShoppingCart className="w-4 h-4" />
                Cart
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}