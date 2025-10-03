import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShoppingCart } from "lucide-react";

interface ProductCardProps {
  id: string;
  name: string;
  price: number;
  image: string;
  brand: string;
  onAddToCart: (productId: string) => void;
}

export default function ProductCard({ id, name, price, image, brand, onAddToCart }: ProductCardProps) {
  const handleAddToCart = () => {
    console.log(`Adding ${name} to cart`); //todo: remove mock functionality
    onAddToCart(id);
  };

  return (
    <Card className="hover-elevate overflow-hidden group" data-testid={`card-product-${id}`}>
      <div className="aspect-square overflow-hidden">
        <img 
          src={image} 
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          data-testid={`img-product-${id}`}
        />
      </div>
      <div className="p-6">
        <div className="mb-2">
          <p className="text-sm text-muted-foreground font-medium" data-testid={`text-brand-${id}`}>
            {brand}
          </p>
          <h3 className="text-lg font-medium text-foreground" data-testid={`text-name-${id}`}>
            {name}
          </h3>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xl font-bold text-foreground" data-testid={`text-price-${id}`}>
            ${price}
          </span>
          <Button 
            onClick={handleAddToCart}
            className="gap-2 h-10 px-4 font-medium"
            data-testid={`button-add-to-cart-${id}`}
          >
            <ShoppingCart className="w-4 h-4" />
            Add to Cart
          </Button>
        </div>
      </div>
    </Card>
  );
}