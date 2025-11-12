import { Navbar } from "@/components/Navbar";
import { ProductCard } from "@/components/ProductCard";
import { useLocation } from "wouter";
import { useProducts } from "@/hooks/use-products";

// Import generated product images (using placeholders)
const macbookAirM2Midnight = "/images/macbook-air-midnight.jpg";
const macbookAirM2Starlight = "/images/macbook-air-starlight.jpg";
const macbookProM3SpaceGrey = "/images/macbook-pro-grey.jpg";
const macbookProM3ProSpaceBlack = "/images/macbook-pro-black.jpg";
const macbookAirM1Silver = "/images/macbook-air-silver.jpg";

// Product images mapping with fallbacks
const productImages: Record<string, string> = {
  // Original hardcoded products
  "B0B94152F6": macbookAirM2Midnight,
  "B0B94213G7": macbookAirM2Starlight,
  "B0CJ5KWD22": macbookProM3SpaceGrey,
  "B0CJ5LSM38": macbookProM3ProSpaceBlack,
  "B08N5XSG8Z": macbookAirM1Silver,
  
  // Additional mappings for database products (fallbacks)
  "B0CHX1W1XY": macbookProM3SpaceGrey, // iPhone 15 Pro Max fallback
  "B0CHX2PDLX": macbookProM3SpaceGrey, // iPhone 15 Pro Max Blue fallback
  "B0CMDRCZBX": macbookAirM2Midnight, // Samsung Galaxy S24 Ultra fallback
  "B0CMDQZPZX": macbookAirM2Starlight, // Samsung Galaxy S24 Ultra Gray fallback
};

// Get appropriate image for product with smart fallbacks
const getProductImage = (product: any): string => {
  // Try direct ASIN mapping first
  if (product.ASIN && productImages[product.ASIN]) {
    return productImages[product.ASIN];
  }
  
  // Smart fallback based on product type
  const modelName = product.Model_Name?.toLowerCase() || product.name?.toLowerCase() || '';
  const color = product.Color?.toLowerCase() || '';
  
  if (modelName.includes('macbook air')) {
    if (color.includes('midnight')) return macbookAirM2Midnight;
    if (color.includes('starlight')) return macbookAirM2Starlight;
    if (color.includes('silver')) return macbookAirM1Silver;
    return macbookAirM2Midnight; // default MacBook Air
  } else if (modelName.includes('macbook pro')) {
    if (color.includes('space black')) return macbookProM3ProSpaceBlack;
    if (color.includes('space grey') || color.includes('space gray')) return macbookProM3SpaceGrey;
    return macbookProM3SpaceGrey; // default MacBook Pro
  } else if (modelName.includes('iphone')) {
    return macbookProM3SpaceGrey; // iPhone placeholder
  } else if (modelName.includes('samsung') || modelName.includes('galaxy')) {
    return macbookAirM2Midnight; // Samsung placeholder
  }
  
  // Ultimate fallback
  return macbookAirM2Midnight;
};

export default function ProductsPage() {
  const [, setLocation] = useLocation();
  
  // Fetch products from database ONLY - no fallback to hardcoded products
  const { data: databaseProducts, isLoading, error } = useProducts();
  
  // Use only database products, empty array if no data
  const products = databaseProducts || [];

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar onLogout={() => {
          localStorage.removeItem("isAuthenticated");
          setLocation("/login");
        }} />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading products...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar onLogout={() => {
          localStorage.removeItem("isAuthenticated");
          setLocation("/login");
        }} />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <p className="text-destructive mb-2">Failed to load products</p>
            <p className="text-muted-foreground text-sm">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

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
              Explore our complete collection of premium products
            </p>
          </div>
        </div>
      </section>

      {/* Products Grid */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        {products.length === 0 ? (
          <div className="text-center py-12">
            <div className="mb-4">
              <div className="mx-auto h-24 w-24 rounded-full bg-muted flex items-center justify-center">
                <span className="text-4xl">📦</span>
              </div>
            </div>
            <h3 className="text-xl font-semibold mb-2">No Products Available</h3>
            <p className="text-muted-foreground mb-4">
              There are no products in the database yet. Please check back later.
            </p>
            <button 
              onClick={() => window.location.reload()} 
              className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Refresh Page
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {products.map((product) => (
              <ProductCard
                key={product.ASIN || product.id || product.name}
                product={product}
                imageSrc={getProductImage(product)}
              /> 
            ))}
          </div>
        )}
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
