import ProductGrid from "@/components/ProductGrid";
import { useToast } from "@/hooks/use-toast";
// todo: remove mock functionality - replace with real product data
import nikeAirMax from "@assets/generated_images/Nike_Air_Max_sneakers_d0062d9e.png";
import adidasUltraBoost from "@assets/generated_images/Adidas_UltraBoost_shoes_d95acb11.png";
import jordan1 from "@assets/generated_images/Jordan_1_basketball_shoes_62dd8242.png";
import converse from "@assets/generated_images/Converse_Chuck_Taylor_shoes_494ce332.png";
import vansOldSkool from "@assets/generated_images/Vans_Old_Skool_shoes_93f89519.png";

const MOCK_PRODUCTS = [
  {
    id: "B0B94152F6",
    name: "MacBook Air M2",
    brand: "Apple",
    price: 110000,
    image: nikeAirMax,
    specs: {
      release_year: 2022,
      ram_gb: 8,
      storage_gb: 256,
      color: "Midnight"
    }
  },
  {
    id: "B0B94213G7",
    name: "MacBook Air M2",
    brand: "Apple",
    price: 140000,
    image: adidasUltraBoost,
    specs: {
      release_year: 2022,
      ram_gb: 16,
      storage_gb: 512,
      color: "Starlight"
    }
  },
  {
    id: "B0CJ5KWD22",
    name: "MacBook Pro M3",
    brand: "Apple",
    price: 169900,
    image: jordan1,
    specs: {
      release_year: 2023,
      ram_gb: 8,
      storage_gb: 512,
      color: "Space Grey"
    }
  },
  {
    id: "B0CJ5LSM38",
    name: "MacBook Pro M3 Pro",
    brand: "Apple",
    price: 199900,
    image: converse,
    specs: {
      release_year: 2023,
      ram_gb: 18,
      storage_gb: 512,
      color: "Space Black"
    }
  },
  {
    id: "B08N5XSG8Z",
    name: "MacBook Air M1",
    brand: "Apple",
    price: 99900,
    image: vansOldSkool,
    specs: {
      release_year: 2020,
      ram_gb: 8,
      storage_gb: 256,
      color: "Silver"
    }
  }
];

interface ShoesPageProps {
  onAddToCart: (productId: string) => void;
}

export default function ShoesPage({ onAddToCart }: ShoesPageProps) {
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
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2" data-testid="text-page-title">
          All Shoes
        </h1>
        <p className="text-muted-foreground" data-testid="text-page-subtitle">
          Browse our complete collection of sneakers and footwear
        </p>
      </div>
      
      <ProductGrid 
        products={MOCK_PRODUCTS} 
        onAddToCart={handleAddToCart}
      />
    </div>
  );
}
