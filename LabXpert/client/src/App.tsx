import { Switch, Route, Redirect, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import { CartProvider } from "@/components/CartProvider";
import { useEffect, useState } from "react";
import LoginPage from "@/pages/login";
import HomePage from "@/pages/home";
import ProductsPage from "@/pages/products";
import CartPage from "@/pages/cart";
import AdminDashboard from "@/pages/AdminDashboard";
import NotFound from "@/pages/not-found";

// ✅ Enhanced Protected Route
function ProtectedRoute({
  component: Component,
  role,
}: {
  component: () => JSX.Element;
  role?: string;
}) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [, setLocation] = useLocation();

  useEffect(() => {
    const auth = localStorage.getItem("isAuthenticated") === "true";
    const user = JSON.parse(localStorage.getItem("user") || "{}");

    if (!auth) {
      setIsAuthenticated(false);
      setLocation("/login");
      return;
    }

    // ✅ Role-based restriction
    if (role && user.role !== role) {
      setLocation("/home");
      return;
    }

    setIsAuthenticated(true);
  }, [role, setLocation]);

  if (isAuthenticated === null) return null;
  return isAuthenticated ? <Component /> : null;
}

function Router() {
  return (
    <Switch>
      <Route path="/login" component={LoginPage} />
      <Route path="/home">
        <ProtectedRoute component={HomePage} />
      </Route>
      <Route path="/products">
        <ProtectedRoute component={ProductsPage} />
      </Route>
      <Route path="/cart">
        <ProtectedRoute component={CartPage} />
      </Route>
      <Route path="/admin">
        <ProtectedRoute component={AdminDashboard} role="admin" /> {/* ✅ */}
      </Route>
      <Route path="/">
        <Redirect to="/login" />
      </Route>
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark">
        <CartProvider>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </CartProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;