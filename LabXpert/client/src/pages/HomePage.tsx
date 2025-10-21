import ProductGrid from "@/components/ProductGrid";
import { useToast } from "@/hooks/use-toast";

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

interface HomePageProps {
  onAddToCart: (productId: string) => void;
  cartItemCount: number;
}

export default function HomePage({ onAddToCart, cartItemCount }: HomePageProps) {
  const { toast } = useToast();

  const handleAddToCart = (productId: string) => {
    onAddToCart(productId);
    const product = MOCK_PRODUCTS.find(p => p.id === productId);
    
    toast({
      title: "Added to Cart",
      description: `${product?.name} has been added to your cart.`,
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-foreground mb-2" data-testid="text-page-title">
          Featured Products
        </h1>
        <p className="text-muted-foreground" data-testid="text-page-subtitle">
          Discover our curated collection of premium MacBooks
        </p>
      </div>
      
      <ProductGrid 
        products={MOCK_PRODUCTS} 
        onAddToCart={handleAddToCart}
      />
      
      {cartItemCount > 0 && (
        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground" data-testid="text-cart-count">
            Items in cart: {cartItemCount}
          </p>
        </div>
      )}
    </div>
  );
}
