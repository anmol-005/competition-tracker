import { Navbar } from "@/components/Navbar";
import { useLocation } from "wouter";
import { ShoppingCart, Trash2, Plus, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useCart } from "@/components/CartProvider";
import { useToast } from "@/hooks/use-toast";

export default function CartPage() {
  const [, setLocation] = useLocation();
  const { items, removeFromCart, updateQuantity, cartTotal, clearCart } = useCart();
  const { toast } = useToast();

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    setLocation("/login");
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(price);
  };

  const handleRemoveItem = (asin: string, modelName: string) => {
    removeFromCart(asin);
    toast({
      title: "Removed from cart",
      description: `${modelName} has been removed from your cart.`,
    });
  };

  const handleClearCart = () => {
    clearCart();
    toast({
      title: "Cart cleared",
      description: "All items have been removed from your cart.",
    });
  };

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar onLogout={handleLogout} />
        
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h1 className="mb-8 text-3xl font-bold text-foreground">Shopping Cart</h1>
          
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="flex h-24 w-24 items-center justify-center rounded-full bg-muted">
                <ShoppingCart className="h-12 w-12 text-muted-foreground" />
              </div>
              <h2 className="mt-6 text-xl font-semibold text-foreground">
                Your cart is empty
              </h2>
              <p className="mt-2 text-center text-muted-foreground">
                Add items to your cart to see them here
              </p>
              <Button
                className="mt-6"
                onClick={() => setLocation("/home")}
                data-testid="button-continue-shopping"
              >
                Continue Shopping
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar onLogout={handleLogout} />
      
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-foreground">
            Shopping Cart ({items.length} {items.length === 1 ? "item" : "items"})
          </h1>
          <Button
            variant="outline"
            onClick={handleClearCart}
            data-testid="button-clear-cart"
          >
            Clear Cart
          </Button>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item) => (
              <Card key={item.product.ASIN} data-testid={`cart-item-${item.product.ASIN}`}>
                <CardContent className="p-6">
                  <div className="flex gap-6">
                    {/* Product Image Placeholder */}
                    <div className="flex-shrink-0">
                      <div className="h-24 w-24 rounded-md bg-muted flex items-center justify-center">
                        <ShoppingCart className="h-8 w-8 text-muted-foreground" />
                      </div>
                    </div>

                    {/* Product Details */}
                    <div className="flex flex-1 flex-col gap-4">
                      <div className="flex justify-between gap-4">
                        <div>
                          <h3 className="text-lg font-semibold text-foreground" data-testid={`text-cart-product-name-${item.product.ASIN}`}>
                            {item.product.Model_Name}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {item.product.Color} • {item.product.RAM_GB}GB RAM • {item.product.Storage_GB}GB Storage
                          </p>
                          <p className="mt-1 text-base font-medium text-foreground">
                            {formatPrice(item.product.Base_Price)}
                          </p>
                        </div>

                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveItem(item.product.ASIN, item.product.Model_Name)}
                          data-testid={`button-remove-${item.product.ASIN}`}
                          aria-label="Remove item"
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-muted-foreground">Quantity:</span>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => updateQuantity(item.product.ASIN, item.quantity - 1)}
                            disabled={item.quantity <= 1}
                            data-testid={`button-decrease-${item.product.ASIN}`}
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                          <span className="min-w-8 text-center font-medium" data-testid={`text-quantity-${item.product.ASIN}`}>
                            {item.quantity}
                          </span>
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => updateQuantity(item.product.ASIN, item.quantity + 1)}
                            data-testid={`button-increase-${item.product.ASIN}`}
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                        <span className="ml-auto text-base font-semibold text-foreground" data-testid={`text-item-subtotal-${item.product.ASIN}`}>
                          {formatPrice(item.product.Base_Price * item.quantity)}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-20">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-xl font-semibold text-foreground">Order Summary</h2>
                
                <Separator />

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="text-foreground" data-testid="text-subtotal">
                      {formatPrice(cartTotal)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className="text-foreground">Free</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tax</span>
                    <span className="text-foreground">Calculated at checkout</span>
                  </div>
                </div>

                <Separator />

                <div className="flex justify-between">
                  <span className="text-lg font-semibold text-foreground">Total</span>
                  <span className="text-2xl font-bold text-primary" data-testid="text-total">
                    {formatPrice(cartTotal)}
                  </span>
                </div>

                <Button className="w-full" size="lg" data-testid="button-checkout">
                  Proceed to Checkout
                </Button>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setLocation("/home")}
                  data-testid="button-continue-shopping-summary"
                >
                  Continue Shopping
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
