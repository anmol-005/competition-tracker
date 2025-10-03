import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShoppingCart, Plus, Minus, Trash2 } from "lucide-react";

// todo: remove mock functionality - replace with real product data
import nikeAirMax from "@assets/generated_images/Nike_Air_Max_sneakers_d0062d9e.png";
import adidasUltraBoost from "@assets/generated_images/Adidas_UltraBoost_shoes_d95acb11.png";
import jordan1 from "@assets/generated_images/Jordan_1_basketball_shoes_62dd8242.png";
import converse from "@assets/generated_images/Converse_Chuck_Taylor_shoes_494ce332.png";
import vansOldSkool from "@assets/generated_images/Vans_Old_Skool_shoes_93f89519.png";

const MOCK_PRODUCTS = [
  {
    id: "1",
    name: "Air Max 270",
    brand: "Nike",
    price: 150,
    image: nikeAirMax
  },
  {
    id: "2", 
    name: "UltraBoost 22",
    brand: "Adidas",
    price: 180,
    image: adidasUltraBoost
  },
  {
    id: "3",
    name: "Air Jordan 1 Retro",
    brand: "Jordan",
    price: 170,
    image: jordan1
  },
  {
    id: "4",
    name: "Chuck Taylor All Star",
    brand: "Converse", 
    price: 65,
    image: converse
  },
  {
    id: "5",
    name: "Old Skool",
    brand: "Vans",
    price: 65,
    image: vansOldSkool
  }
];

interface CartItem {
  id: string;
  name: string;
  brand: string;
  price: number;
  image: string;
  quantity: number;
}

interface CartPageProps {
  cartItems: string[];
  setCartItems: (items: string[]) => void;
}

export default function CartPage({ cartItems: cartItemIds, setCartItems }: CartPageProps) {
  // Convert cart item IDs to full cart items with quantities
  const cartItems = useMemo(() => {
    const itemCounts = cartItemIds.reduce((acc, id) => {
      acc[id] = (acc[id] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(itemCounts).map(([id, quantity]) => {
      const product = MOCK_PRODUCTS.find(p => p.id === id);
      return {
        id,
        name: product?.name || '',
        brand: product?.brand || '',
        price: product?.price || 0,
        image: product?.image || '',
        quantity
      } as CartItem;
    }).filter(item => item.name); // Filter out items where product wasn't found
  }, [cartItemIds]);

  const updateQuantity = (id: string, change: number) => {
    const currentCount = cartItemIds.filter(itemId => itemId === id).length;
    const newCount = Math.max(0, currentCount + change);
    
    const otherItems = cartItemIds.filter(itemId => itemId !== id);
    const newItems = [...otherItems, ...Array(newCount).fill(id)];
    
    setCartItems(newItems);
  };

  const removeItem = (id: string) => {
    setCartItems(cartItemIds.filter(itemId => itemId !== id));
  };

  const total = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  if (cartItems.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-16">
          <ShoppingCart className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-foreground mb-2" data-testid="text-empty-cart">
            Your cart is empty
          </h1>
          <p className="text-muted-foreground mb-6">
            Start shopping to add items to your cart
          </p>
          <Button className="gap-2 h-11 px-6 font-medium" data-testid="button-continue-shopping">
            <ShoppingCart className="w-4 h-4" />
            Continue Shopping
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2" data-testid="text-page-title">
          Shopping Cart
        </h1>
        <p className="text-muted-foreground" data-testid="text-page-subtitle">
          Review your items before checkout
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {cartItems.map((item) => (
            <Card key={item.id} className="p-6" data-testid={`card-cart-item-${item.id}`}>
              <div className="flex items-center gap-4">
                <img 
                  src={item.image} 
                  alt={item.name}
                  className="w-20 h-20 object-cover rounded-lg"
                  data-testid={`img-cart-item-${item.id}`}
                />
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground font-medium" data-testid={`text-brand-${item.id}`}>
                    {item.brand}
                  </p>
                  <h3 className="font-medium text-foreground" data-testid={`text-name-${item.id}`}>
                    {item.name}
                  </h3>
                  <p className="font-bold text-foreground" data-testid={`text-price-${item.id}`}>
                    ${item.price}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => updateQuantity(item.id, -1)}
                    data-testid={`button-decrease-${item.id}`}
                  >
                    <Minus className="w-4 h-4" />
                  </Button>
                  <span className="w-8 text-center font-medium" data-testid={`text-quantity-${item.id}`}>
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
                <span className="font-medium" data-testid="text-subtotal">${total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Shipping</span>
                <span className="font-medium text-accent">Free</span>
              </div>
              <div className="border-t pt-2">
                <div className="flex justify-between">
                  <span className="font-semibold text-foreground">Total</span>
                  <span className="font-bold text-lg" data-testid="text-total">${total.toFixed(2)}</span>
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