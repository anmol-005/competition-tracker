import { Link, useLocation } from "wouter";
import { Home, ShoppingCart, LogOut, Laptop } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "./ThemeToggle";
import { useCart } from "./CartProvider";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NavbarProps {
  onLogout: () => void;
}

export function Navbar({ onLogout }: NavbarProps) {
  const [location, setLocation] = useLocation();
  const { cartCount } = useCart();

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/home">
          <div className="flex items-center gap-2 hover-elevate active-elevate-2 rounded-md px-3 py-2 transition-all cursor-pointer" data-testid="link-logo">
            <Laptop className="h-6 w-6 text-primary" />
            <span className="text-2xl font-bold">
              <span className="text-primary">Lap</span>
              <span className="text-foreground">Xpert</span>
            </span>
          </div>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-2">
          <Button
            variant={location === "/home" ? "default" : "ghost"}
            size="default"
            className="gap-2"
            onClick={() => setLocation("/home")}
            data-testid="link-home"
          >
            <Home className="h-4 w-4" />
            <span className="hidden sm:inline">Home</span>
          </Button>

          <Button
            variant={location === "/products" ? "default" : "ghost"}
            size="default"
            className="gap-2"
            onClick={() => setLocation("/products")}
            data-testid="link-products"
          >
            <Laptop className="h-4 w-4" />
            <span className="hidden sm:inline">Products</span>
          </Button>

          {cartCount > 0 ? (
            <Button
              variant={location === "/cart" ? "default" : "ghost"}
              size="default"
              className="gap-2 relative"
              onClick={() => setLocation("/cart")}
              data-testid="link-cart"
            >
              <ShoppingCart className="h-4 w-4" />
              <span className="hidden sm:inline">Cart</span>
              {cartCount > 0 && (
                <Badge
                  variant="destructive"
                  className="absolute -right-1 -top-1 h-5 min-w-5 px-1 text-xs"
                  data-testid="text-cart-count"
                >
                  {cartCount}
                </Badge>
              )}
            </Button>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <Button
                    variant="ghost"
                    size="default"
                    className="gap-2 opacity-40 cursor-not-allowed"
                    disabled
                    data-testid="link-cart"
                    aria-label="Cart (Add items to enable)"
                  >
                    <ShoppingCart className="h-4 w-4" />
                    <span className="hidden sm:inline">Cart</span>
                  </Button>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Add items to enable cart</p>
              </TooltipContent>
            </Tooltip>
          )}

          <Button
            variant="ghost"
            size="default"
            onClick={onLogout}
            className="gap-2"
            data-testid="button-logout"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </Button>

          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
