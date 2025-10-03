import { useState } from "react";
import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Navbar from "@/components/Navbar";
import LoginPage from "@/pages/LoginPage";
import HomePage from "@/pages/HomePage";
import ShoesPage from "@/pages/ShoesPage";
import CartPage from "@/pages/CartPage";
import NotFound from "@/pages/not-found";

function Router() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [cartItems, setCartItems] = useState<string[]>([]);
  const [, setLocation] = useLocation();

  const handleLogin = (email: string, password: string) => {
    console.log("Login successful:", { email }); //todo: remove mock functionality
    setIsLoggedIn(true);
    setLocation("/home");
  };

  const handleLogout = () => {
    console.log("User logged out"); //todo: remove mock functionality
    setIsLoggedIn(false);
    setCartItems([]);
    setLocation("/login");
  };

  const handleAddToCart = (productId: string) => {
    setCartItems(prev => [...prev, productId]);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar isLoggedIn={isLoggedIn} onLogout={handleLogout} cartItemCount={cartItems.length} />
      
      <Switch>
        <Route path="/login">
          <LoginPage onLogin={handleLogin} />
        </Route>
        <Route path="/home">
          {isLoggedIn ? <HomePage onAddToCart={handleAddToCart} cartItemCount={cartItems.length} /> : <LoginPage onLogin={handleLogin} />}
        </Route>
        <Route path="/shoes">
          {isLoggedIn ? <ShoesPage onAddToCart={handleAddToCart} /> : <LoginPage onLogin={handleLogin} />}
        </Route>
        <Route path="/cart">
          {isLoggedIn ? <CartPage cartItems={cartItems} setCartItems={setCartItems} /> : <LoginPage onLogin={handleLogin} />}
        </Route>
        <Route path="/">
          {isLoggedIn ? <HomePage onAddToCart={handleAddToCart} cartItemCount={cartItems.length} /> : <LoginPage onLogin={handleLogin} />}
        </Route>
        <Route component={NotFound} />
      </Switch>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
