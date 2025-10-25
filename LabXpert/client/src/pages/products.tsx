import { Navbar } from "@/components/Navbar";
import { ProductCard } from "@/components/ProductCard";
import { PRODUCTS } from "@shared/schema";
import { useLocation } from "wouter";

// Import generated product images
import macbookAirM2Midnight from "@assets/generated_images/MacBook_Air_M2_Midnight_5dac8d92.png";
import macbookAirM2Starlight from "@assets/generated_images/MacBook_Air_M2_Starlight_29ce1c6c.png";
import macbookProM3SpaceGrey from "@assets/generated_images/MacBook_Pro_M3_Space_Grey_62b40ab3.png";
import macbookProM3ProSpaceBlack from "@assets/generated_images/MacBook_Pro_M3_Pro_Space_Black_faacdddf.png";
import macbookAirM1Silver from "@assets/generated_images/MacBook_Air_M1_Silver_a8b9d4df.png";

const productImages: Record<string, string> = {
  "B0B94152F6": macbookAirM2Midnight,
  "B0B94213G7": macbookAirM2Starlight,
  "B0CJ5KWD22": macbookProM3SpaceGrey,
  "B0CJ5LSM38": macbookProM3ProSpaceBlack,
  "B08N5XSG8Z": macbookAirM1Silver,
};

export default function ProductsPage() {
  const [, setLocation] = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    setLocation("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar onLogout={handleLogout} />

      {/* Page Header */}
      <section className="border-b bg-muted/30 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-foreground sm:text-5xl">
              All Products
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Explore our complete collection of premium MacBook laptops
            </p>
          </div>
        </div>
      </section>

      {/* Products Grid */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">
            Showing <span className="font-medium text-foreground">{PRODUCTS.length}</span> products
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
