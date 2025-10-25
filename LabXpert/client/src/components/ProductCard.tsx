import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingCart, Cpu, HardDrive, Calendar, Palette } from "lucide-react";
import { useCart } from "@/components/CartProvider";
import { useToast } from "@/hooks/use-toast";
import type { Product } from "@shared/schema";

interface ProductCardProps {
  product: Product;
  imageSrc: string;
}

export function ProductCard({ product, imageSrc }: ProductCardProps) {
  const { addToCart } = useCart();
  const { toast } = useToast();

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(price);
  };

  const handleAddToCart = () => {
    addToCart(product);
    toast({
      title: "Added to cart",
      description: `${product.Model_Name} (${product.Color}) has been added to your cart.`,
    });
  };

  return (
    <Card className="group overflow-visible hover-elevate transition-all duration-200 hover:shadow-xl">
      <CardHeader className="p-0">
        <div className="aspect-[4/3] overflow-hidden rounded-t-lg bg-muted">
          <img
            src={imageSrc}
            alt={`${product.Model_Name} ${product.Color}`}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            data-testid={`img-product-${product.ASIN}`}
          />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4 p-6">
        {/* Product Title */}
        <div>
          <h3 className="text-xl font-semibold text-foreground" data-testid={`text-model-${product.ASIN}`}>
            {product.Model_Name}
          </h3>
          <Badge variant="secondary" className="mt-2">
            {product.Color}
          </Badge>
        </div>

        {/* Specifications Grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">RAM</p>
              <p className="font-medium text-foreground" data-testid={`text-ram-${product.ASIN}`}>
                {product.RAM_GB} GB
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
            <HardDrive className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Storage</p>
              <p className="font-medium text-foreground" data-testid={`text-storage-${product.ASIN}`}>
                {product.Storage_GB} GB
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Year</p>
              <p className="font-medium text-foreground" data-testid={`text-year-${product.ASIN}`}>
                {product.Release_Year}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
            <Palette className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Color</p>
              <p className="font-medium text-foreground truncate" data-testid={`text-color-${product.ASIN}`}>
                {product.Color}
              </p>
            </div>
          </div>
        </div>

        {/* Price */}
        <div className="pt-2">
          <p className="text-2xl font-bold text-primary" data-testid={`text-price-${product.ASIN}`}>
            {formatPrice(product.Base_Price)}
          </p>
        </div>
      </CardContent>

      <CardFooter className="p-6 pt-0">
        <Button
          className="w-full gap-2"
          size="default"
          onClick={handleAddToCart}
          data-testid={`button-add-to-cart-${product.ASIN}`}
        >
          <ShoppingCart className="h-4 w-4" />
          Add to Cart
        </Button>
      </CardFooter>
    </Card>
  );
}
