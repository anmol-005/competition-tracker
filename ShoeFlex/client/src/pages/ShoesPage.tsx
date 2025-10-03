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