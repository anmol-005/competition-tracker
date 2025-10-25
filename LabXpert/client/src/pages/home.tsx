import { Navbar } from "@/components/Navbar";
import { ProductCard } from "@/components/ProductCard";
import { PRODUCTS } from "@shared/schema";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

// Import generated product images
import macbookAirM2Midnight from "@assets/generated_images/MacBook_Air_M2_Midnight_5dac8d92.png";
import macbookAirM2Starlight from "@assets/generated_images/MacBook_Air_M2_Starlight_29ce1c6c.png";
import macbookProM3SpaceGrey from "@assets/generated_images/MacBook_Pro_M3_Space_Grey_62b40ab3.png";
import macbookProM3ProSpaceBlack from "@assets/generated_images/MacBook_Pro_M3_Pro_Space_Black_faacdddf.png";
import macbookAirM1Silver from "@assets/generated_images/MacBook_Air_M1_Silver_a8b9d4df.png";
import heroImage from "@assets/generated_images/Hero_workspace_MacBook_banner_14301a3a.png";

const productImages: Record<string, string> = {
  "B0B94152F6": macbookAirM2Midnight,
  "B0B94213G7": macbookAirM2Starlight,
  "B0CJ5KWD22": macbookProM3SpaceGrey,
  "B0CJ5LSM38": macbookProM3ProSpaceBlack,
  "B08N5XSG8Z": macbookAirM1Silver,
};

export default function HomePage() {
  const [, setLocation] = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    setLocation("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar onLogout={handleLogout} />
      
      {/* Hero Section */}
      <section className="relative h-[60vh] md:h-[70vh] overflow-hidden">
        <div className="absolute inset-0">
          <img
            src={heroImage}
            alt="MacBook workspace"
            className="h-full w-full object-cover"
          />
          {/* Dark wash overlay for text readability */}
          <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-black/50 to-black/70" />
        </div>
        
        <div className="relative z-10 mx-auto flex h-full max-w-7xl flex-col items-center justify-center px-4 text-center sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-white sm:text-5xl md:text-6xl lg:text-7xl">
            Welcome to <span className="text-primary">LapXpert</span>
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-white/90 sm:text-xl md:text-2xl">
            Discover premium MacBook laptops curated by experts
          </p>
          <Button
            size="lg"
            className="mt-8 gap-2 bg-primary/90 backdrop-blur-sm"
            onClick={() => {
              document.getElementById("products")?.scrollIntoView({ behavior: "smooth" });
            }}
            data-testid="button-browse-collection"
          >
            Browse Collection
            <ArrowRight className="h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Products Section */}
      <section id="products" className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-foreground sm:text-4xl">
            Our Premium Collection
          </h2>
          <p className="mt-2 text-lg text-muted-foreground">
            Choose from the latest MacBook Air and MacBook Pro models
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {PRODUCTS.map((product) => (
            <ProductCard
              key={product.ASIN}
              product={product}
              imageSrc={productImages[product.ASIN]}
            />
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-muted/30 py-8">
        <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} LapXpert. Premium MacBooks, Expert Choice.
          </p>
        </div>
      </footer>
    </div>
  );
}
