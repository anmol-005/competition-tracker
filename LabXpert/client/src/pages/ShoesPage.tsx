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
    name: "MacBook Air M2",
    brand: "Apple",
    price: 110000,
    image: macbookImage,
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
    image: mce,
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
    image: mde,
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
    image: mvde,
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
    image: mffe,
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
