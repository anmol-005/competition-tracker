import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShoppingCart, Plus, Minus, Trash2 } from "lucide-react";

// todo: remove mock functionality - replace with real product data
import macbookImage from "@assets/generated_images/CMC_1580.jpg";
import mce from "@assets/generated_images/download (1).jpg";
import mde from "@assets/generated_images/download.jpg";
import mvde from "@assets/generated_images/OIP (1).jpg";
import mffe from "@assets/generated_images/OIP.jpg"

const MOCK_PRODUCTS = [
  {
    id: "B0B94152F6",
    name: "MacBook Air M2 8GB/256GB",
    brand: "Apple",
    price: 110000,
    image: macbookImage,
    description: "Midnight"
  },
  {
    id: "B0B94213G7",
    name: "MacBook Air M2 16GB/512GB",
    brand: "Apple",
    price: 140000,
    image: mce,
    description: "Starlight"
  },
  {
    id: "B0CJ5KWD22",
    name: "MacBook Pro M3 8GB/512GB",
    brand: "Apple",
    price: 169900,
    image: mde,
    description: "Space Grey"
  },
  {
    id: "B0CJ5LSM38",
    name: "MacBook Pro M3 Pro 18GB/512GB",
    brand: "Apple",
    price: 199900,
    image: mvde,
    description: "Space Black"
  },
  {
    id: "B08N5XSG8Z",
    name: "MacBook Air M1 8GB/256GB",
    brand: "Apple",
    price: 99900,
    image: mffe,
    description: "Silver"
  }
];

interface CartItem {
  id: string;
  quantity: number;
}

interface CartPageProps {
  cartItems: CartItem[];
  onUpdateQuantity: (productId: string, change: number) => void;
  onRemoveItem: (productId: string) => void;
}

export default function CartPage({ 
  cartItems, 
  onUpdateQuantity, 
  onRemoveItem 
}: CartPageProps) {
  const cartWithProducts = useMemo(() => {
    return cartItems.map(item => ({
      ...item,
      product: MOCK_PRODUCTS.find(p => p.id === item.id)
    })).filter(item => item.product);
  }, [cartItems]);

  const total = useMemo(() => {
    return cartWithProducts.reduce((sum, item) => {
      return sum + (item.product?.price || 0) * item.quantity;
    }, 0);
  }, [cartWithProducts]);

  const updateQuantity = (productId: string, change: number) => {
    onUpdateQuantity(productId, change);
  };

  const removeItem = (productId: string) => {
    onRemoveItem(productId);
  };

  if (cartItems.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-16" data-testid="empty-cart">
          <ShoppingCart className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold text-foreground mb-2" data-testid="text-empty-cart-title">
            Your cart is empty
          </h2>
          <p className="text-muted-foreground" data-testid="text-empty-cart-subtitle">
            Start shopping to add items to your cart
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-foreground mb-8" data-testid="text-cart-title">
        Shopping Cart
      </h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4" data-testid="cart-items-list">
          {cartWithProducts.map((item) => (
            <Card key={item.id} className="p-4" data-testid={`cart-item-${item.id}`}>
              <div className="flex gap-4">
                <img 
                  src={item.product?.image} 
                  alt={item.product?.name}
                  className="w-24 h-24 object-cover rounded"
                  data-testid={`cart-item-image-${item.id}`}
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground" data-testid={`cart-item-name-${item.id}`}>
                    {item.product?.name}
                  </h3>
                  <p className="text-sm text-muted-foreground" data-testid={`cart-item-brand-${item.id}`}>
                    {item.product?.brand}
                  </p>
                  {item.product?.description && (
                    <p className="text-sm text-muted-foreground" data-testid={`cart-item-description-${item.id}`}>
                      {item.product.description}
                    </p>
                  )}
                  <p className="text-lg font-bold text-foreground mt-2" data-testid={`cart-item-price-${item.id}`}>
                    ₹{item.product?.price.toLocaleString()}
                  </p>
                </div>
                <div className="flex flex-col items-end justify-between">
                  <p className="font-semibold text-foreground" data-testid={`cart-item-total-${item.id}`}>
                    ₹{((item.product?.price || 0) * item.quantity).toLocaleString()}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="icon"
                      onClick={() => updateQuantity(item.id, -1)}
                      disabled={item.quantity <= 1}
                      data-testid={`button-decrease-${item.id}`}
                    >
                      <Minus className="w-4 h-4" />
                    </Button>
                    <span className="w-8 text-center" data-testid={`cart-item-quantity-${item.id}`}>
                      {item.quantity}
                    </span>
                    <Button 
                      variant="outline" 
                      size="icon"
                      onClick={() => updateQuantity(item.id, 1)}
                      data-testid={`button-increase-${item.id}`}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="icon"
                      onClick={() => removeItem(item.id)}
                      className="ml-2 text-destructive hover:text-destructive"
                      data-testid={`button-remove-${item.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
        <div className="lg:col-span-1">
          <Card className="p-6 sticky top-24">
            <h3 className="text-lg font-semibold text-foreground mb-4" data-testid="text-order-summary">
              Order Summary
            </h3>
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-medium" data-testid="text-subtotal">₹{total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Shipping</span>
                <span className="font-medium text-accent">Free</span>
              </div>
              <div className="border-t pt-2">
                <div className="flex justify-between">
                  <span className="font-semibold text-foreground">Total</span>
                  <span className="font-bold text-lg" data-testid="text-total">₹{total.toLocaleString()}</span>
                </div>
              </div>
            </div>
            <Button className="w-full h-11 font-medium" data-testid="button-checkout">
              Proceed to Checkout
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
