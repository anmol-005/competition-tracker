import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { triggerScraping, useScrapingSessions, predictPrice } from "@/hooks/use-admin-api";
import ScrapingResultsAnalytics from "@/components/ScrapingResultsAnalytics";

/* ---------- Inline Spinner (self-contained) ---------- */
function InlineSpinner({ size = 18 }: { size?: number }) {
  const border = Math.max(2, Math.round(size / 8));
  return (
    <div
      style={{
        width: size,
        height: size,
        border: `${border}px solid rgba(255,255,255,0.12)`,
        borderTop: `${border}px solid rgba(255,255,255,0.9)`,
        borderRadius: "50%",
        display: "inline-block",
        animation: "spin 0.9s linear infinite",
      }}
    />
  );
}

const styleNodeId = "inline-spinner-keyframes";
if (typeof window !== "undefined" && !document.getElementById(styleNodeId)) {
  const style = document.createElement("style");
  style.id = styleNodeId;
  style.innerHTML = `@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`;
  document.head.appendChild(style);
}

/* ---------- Types ---------- */
interface PlatformInfo {
  price?: number | null;
  url?: string | null;
}

interface NormalizedProduct {
  id: string | null;
  name: string;
  platforms: Record<string, PlatformInfo>;
  pricing_summary: {
    lowest_price?: number | null;
    highest_price?: number | null;
    best_platform?: string | null;
  };
  _raw?: any;
}

/* ---------- Helpers: safeNumber and normalizer for your DB shape ---------- */
function safeNumber(v: any): number | null {
  if (v == null) return null;
  if (typeof v === "number") return v;
  // remove currency symbols, commas etc.
  const s = String(v).replace(/[^\d.-]/g, "");
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function normalizeProductForYourDB(raw: any): NormalizedProduct {
  // ID: prefer ASIN if present
  const id = raw.ASIN ?? raw.asin ?? raw.id ?? raw._id ?? null;

  // Name: your DB uses Model_Name
  const name =
    raw.Model_Name ??
    raw.model_name ??
    raw.title ??
    raw.name ??
    raw.product_name ??
    raw.productTitle ??
    "Unnamed product";

  // Handle pricing from multiple possible structures
  let platforms: Record<string, PlatformInfo> = {};
  let pricing_summary = {
    lowest_price: null as number | null,
    highest_price: null as number | null,
    best_platform: null as string | null,
  };

  // Case 1: Direct pricing_summary exists (our enhanced backend structure)
  if (raw.pricing_summary && typeof raw.pricing_summary === 'object') {
    pricing_summary = {
      lowest_price: safeNumber(raw.pricing_summary.lowest_price),
      highest_price: safeNumber(raw.pricing_summary.highest_price),
      best_platform: raw.pricing_summary.best_platform,
    };
  }

  // Case 2: Direct platform pricing (our enhanced backend structure)
  if (raw.platforms && typeof raw.platforms === 'object') {
    Object.entries(raw.platforms).forEach(([platform, data]: [string, any]) => {
      platforms[platform] = {
        price: safeNumber(data?.price ?? data?.current_price ?? data?.amount),
        url: data?.url ?? data?.link ?? null
      };
    });
  } else {
    // Case 3: Legacy structure - build platforms from individual price fields
    platforms['our_store'] = {
      price: safeNumber(raw.our_price ?? raw.price ?? raw.current_price ?? raw.Price),
      url: raw.url ?? null
    };

    // Add Amazon data if present
    if (raw.amazon_price || raw.Amazon_Price) {
      platforms['Amazon'] = {
        price: safeNumber(raw.amazon_price ?? raw.Amazon_Price),
        url: raw.amazon_url ?? null
      };
    }

    // Add Smartprix data if present  
    if (raw.smartprix_price || raw.Smartprix_Price) {
      platforms['Smartprix'] = {
        price: safeNumber(raw.smartprix_price ?? raw.Smartprix_Price),
        url: raw.smartprix_url ?? null
      };
    }

    // Add Flipkart data if present
    if (raw.flipkart_price || raw.Flipkart_Price) {
      platforms['Flipkart'] = {
        price: safeNumber(raw.flipkart_price ?? raw.Flipkart_Price),
        url: raw.flipkart_url ?? null
      };
    }
  }

  // Calculate pricing summary if not provided
  if (!pricing_summary.lowest_price || !pricing_summary.highest_price) {
    const allPrices = Object.values(platforms)
      .map(p => p?.price)
      .filter((price): price is number => typeof price === 'number');
    
    if (allPrices.length > 0) {
      pricing_summary.lowest_price = pricing_summary.lowest_price ?? Math.min(...allPrices);
      pricing_summary.highest_price = pricing_summary.highest_price ?? Math.max(...allPrices);
    }
  }

  return { id, name, platforms, pricing_summary, _raw: raw };
}

/* ---------- Helper Functions ---------- */
const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/* ---------- Main Component ---------- */
export default function ProductScraperManagement() {
  const [isTriggering, setIsTriggering] = useState(false);
  const [products, setProducts] = useState<NormalizedProduct[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [predictionResults, setPredictionResults] = useState<Record<string, any>>({});
  const [predictingIds, setPredictingIds] = useState<Set<string>>(new Set());

  const { data: scrapingSessions, isLoading: isLoadingSessions } = useScrapingSessions();

  /* ---------- Fetch Products ---------- */
  const fetchProducts = async () => {
    setLoadingProducts(true);
    try {
      const response = await fetch(`${API_BASE}/products`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch products: ${response.status}`);
      }

      const data = await response.json();
      const rawProducts = data.products || data || [];
      
      const normalizedProducts = rawProducts.map(normalizeProductForYourDB);
      
      setProducts(normalizedProducts);
    } catch (error) {
      console.error('Error fetching products:', error);
      setProducts([]);
    } finally {
      setLoadingProducts(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  /* ---------- Trigger Scraping ---------- */
  const handleTriggerScraping = async () => {
    setIsTriggering(true);
    try {
      const result = await triggerScraping();
      console.log('Scraping result:', result);
      // Refetch products after scraping
      setTimeout(fetchProducts, 2000);
    } catch (error) {
      console.error('Scraping error:', error);
    } finally {
      setIsTriggering(false);
    }
  };

  /* ---------- Predict Price for Product ---------- */
  const handlePredictPrice = async (product: NormalizedProduct) => {
    const productId = product.id || product.name;
    if (!productId) return;

    setPredictingIds(prev => new Set(prev).add(productId));

    try {
      const result = await predictPrice(productId);
      setPredictionResults(prev => ({
        ...prev,
        [productId]: result
      }));
    } catch (error) {
      console.error('Prediction error:', error);
    } finally {
      setPredictingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(productId);
        return newSet;
      });
    }
  };

  /* ---------- Format Currency ---------- */
  const formatCurrency = (amount: number | null | undefined): string => {
    if (amount == null) return '—';
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  /* ---------- Get Best Price Info ---------- */
  const getBestPriceInfo = (product: NormalizedProduct) => {
    const bestPrice = product.pricing_summary?.lowest_price;
    const bestPlatform = product.pricing_summary?.best_platform;
    
    if (bestPrice && bestPlatform) {
      return {
        price: bestPrice,
        platform: bestPlatform,
        formatted: formatCurrency(bestPrice)
      };
    }

    // Fallback: find manually
    const platformEntries = Object.entries(product.platforms);
    const validPrices = platformEntries
      .filter(([_, info]) => typeof info.price === 'number')
      .sort(([_, a], [__, b]) => (a.price as number) - (b.price as number));

    if (validPrices.length > 0) {
      const [platform, info] = validPrices[0];
      return {
        price: info.price,
        platform,
        formatted: formatCurrency(info.price)
      };
    }

    return { price: null, platform: null, formatted: '—' };
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Product Scraper Management</h1>
        <div className="flex gap-3">
          <Button 
            onClick={fetchProducts} 
            variant="outline"
            disabled={loadingProducts}
          >
            {loadingProducts ? <InlineSpinner size={16} /> : 'Refresh Products'}
          </Button>
          <Button 
            onClick={handleTriggerScraping}
            disabled={isTriggering}
          >
            {isTriggering ? <InlineSpinner size={16} /> : 'Trigger Scraping'}
          </Button>
        </div>
      </div>

      {/* Scraping Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Scraping Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingSessions ? (
            <div className="flex items-center justify-center py-8">
              <InlineSpinner size={24} />
              <span className="ml-2">Loading sessions...</span>
            </div>
          ) : (
            <ScrapingResultsAnalytics sessions={scrapingSessions || []} />
          )}
        </CardContent>
      </Card>

      {/* Products List */}
      <Card>
        <CardHeader>
          <CardTitle>Products ({products.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingProducts ? (
            <div className="flex items-center justify-center py-8">
              <InlineSpinner size={24} />
              <span className="ml-2">Loading products...</span>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No products found. Try triggering a scraping session.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.map((product) => {
                const productKey = product.id || product.name;
                const bestPriceInfo = getBestPriceInfo(product);
                const isPredicting = predictingIds.has(productKey);
                const prediction = predictionResults[productKey];

                return (
                  <Card key={productKey} className="border">
                    <CardContent className="p-4">
                      <h3 className="font-semibold text-sm mb-2 line-clamp-2">
                        {product.name}
                      </h3>
                      
                      {product.id && (
                        <p className="text-xs text-muted-foreground mb-2">
                          ID: {product.id}
                        </p>
                      )}

                      <div className="space-y-2 mb-3">
                        <div className="text-xs">
                          <strong>Best Price:</strong> {bestPriceInfo.formatted}
                          {bestPriceInfo.platform && (
                            <span className="text-muted-foreground"> ({bestPriceInfo.platform})</span>
                          )}
                        </div>

                        <div className="text-xs space-y-1">
                          <strong>All Platforms:</strong>
                          {Object.entries(product.platforms).map(([platform, info]) => (
                            <div key={platform} className="flex justify-between">
                              <span>{platform}:</span>
                              <span>{formatCurrency(info.price)}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="w-full"
                        onClick={() => handlePredictPrice(product)}
                        disabled={isPredicting}
                      >
                        {isPredicting ? (
                          <>
                            <InlineSpinner size={14} />
                            <span className="ml-2">Predicting...</span>
                          </>
                        ) : (
                          'Predict Price'
                        )}
                      </Button>

                      {prediction && (
                        <div className="mt-3 p-2 bg-secondary rounded text-xs">
                          <div><strong>Predicted:</strong> {formatCurrency(prediction.predicted_price)}</div>
                          <div><strong>Strategy:</strong> {prediction.pricing_strategy}</div>
                          {prediction.rationale && (
                            <div className="mt-1 text-muted-foreground">
                              {prediction.rationale}
                            </div>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
    // Case 3: Legacy structure - build platforms from individual price fields
    platforms['our_store'] = {
      price: safeNumber(raw.our_price ?? raw.price ?? raw.current_price ?? raw.Price),
      url: raw.url ?? null
    };

    // Add Amazon data if present
    if (raw.amazon_price || raw.Amazon_Price) {
      platforms['Amazon'] = {
        price: safeNumber(raw.amazon_price ?? raw.Amazon_Price),
        url: raw.amazon_url ?? null
      };
    }

    // Add Smartprix data if present  
    if (raw.smartprix_price || raw.Smartprix_Price) {
      platforms['Smartprix'] = {
        price: safeNumber(raw.smartprix_price ?? raw.Smartprix_Price),
        url: raw.smartprix_url ?? null
      };
    }

    // Add Flipkart data if present
    if (raw.flipkart_price || raw.Flipkart_Price) {
      platforms['Flipkart'] = {
        price: safeNumber(raw.flipkart_price ?? raw.Flipkart_Price),
        url: raw.flipkart_url ?? null
      };
    }
  }

  // Calculate pricing summary if not provided
  if (!pricing_summary.lowest_price || !pricing_summary.highest_price) {
    const allPrices = Object.values(platforms)
      .map(p => p?.price)
      .filter((price): price is number => typeof price === 'number');
    
    if (allPrices.length > 0) {
      pricing_summary.lowest_price = pricing_summary.lowest_price ?? Math.min(...allPrices);
      pricing_summary.highest_price = pricing_summary.highest_price ?? Math.max(...allPrices);
    }
  }

  return { id, name, platforms, pricing_summary, _raw: raw };
}

/* ---------- Helper Functions ---------- */
const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/* ---------- Component ---------- */
export default function ProductScraperManagement(): JSX.Element {
  const [products, setProducts] = useState<NormalizedProduct[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [predictingId, setPredictingId] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<Record<string, any>>({});

  // ✅ NEW: Scraper trigger functionality  
  const [scrapingStatus, setScrapingStatus] = useState<Record<string, string>>({});
  const [amazonSearchTerms, setAmazonSearchTerms] = useState('MacBook Pro, iPhone 15, Samsung Galaxy');
  const [smartprixSearchTerms, setSmartprixSearchTerms] = useState('MacBook Pro, iPhone 15, laptop');
  const [flipkartSearchTerms, setFlipkartSearchTerms] = useState('MacBook Pro, iPhone 15, laptop');
  
  // Get scraping sessions data
  const { sessions, loading: sessionsLoading, refetch: refetchSessions } = useScrapingSessions();

  useEffect(() => {
    fetchProducts();
  }, []);

  // ✅ NEW: Scraper trigger functions
  const handleAmazonScraping = async () => {
    setScrapingStatus(prev => ({ ...prev, amazon: 'running' }));
    
    try {
      const searchTermsArray = amazonSearchTerms.split(',').map(term => term.trim());
      
      // Call each search term separately (since our API accepts one product_name at a time)
      let totalSuccess = 0;
      for (const productName of searchTermsArray) {
        try {
          const response = await fetch(`${API_BASE}/scraping/amazon`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              platform: 'amazon',
              product_name: productName
            }),
            credentials: 'include'
          });
          
          const result = await response.json();
          if (response.ok && result.total_products > 0) {
            totalSuccess++;
          }
        } catch (err) {
          console.error(`Amazon scraping failed for ${productName}:`, err);
        }
      }
      
      if (totalSuccess > 0) {
        setScrapingStatus(prev => ({ ...prev, amazon: 'success' }));
        setTimeout(() => {
          refetchSessions();
          fetchProducts();
        }, 2000);
      } else {
        setScrapingStatus(prev => ({ ...prev, amazon: 'error' }));
      }
    } catch (error) {
      console.error('Amazon scraping error:', error);
      setScrapingStatus(prev => ({ ...prev, amazon: 'error' }));
    }
    
    // Reset status after 5 seconds
    setTimeout(() => {
      setScrapingStatus(prev => ({ ...prev, amazon: '' }));
    }, 5000);
  };

  const handleSmartprixScraping = async () => {
    setScrapingStatus(prev => ({ ...prev, smartprix: 'running' }));
    
    try {
      const searchTermsArray = smartprixSearchTerms.split(',').map(term => term.trim());
      
      // Call each search term separately
      let totalSuccess = 0;
      for (const productName of searchTermsArray) {
        try {
          const response = await fetch(`${API_BASE}/scraping/smartprix`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              platform: 'smartprix',
              product_name: productName
            }),
            credentials: 'include'
          });
          
          const result = await response.json();
          if (response.ok && result.total_products > 0) {
            totalSuccess++;
          }
        } catch (err) {
          console.error(`Smartprix scraping failed for ${productName}:`, err);
        }
      }
      
      if (totalSuccess > 0) {
        setScrapingStatus(prev => ({ ...prev, smartprix: 'success' }));
        setTimeout(() => {
          refetchSessions();
          fetchProducts();
        }, 2000);
      } else {
        setScrapingStatus(prev => ({ ...prev, smartprix: 'error' }));
      }
    } catch (error) {
      console.error('Smartprix scraping error:', error);
      setScrapingStatus(prev => ({ ...prev, smartprix: 'error' }));
    }
    
    setTimeout(() => {
      setScrapingStatus(prev => ({ ...prev, smartprix: '' }));
    }, 5000);
  };

  const handleFlipkartScraping = async () => {
    setScrapingStatus(prev => ({ ...prev, flipkart: 'running' }));
    
    try {
      const searchTermsArray = flipkartSearchTerms.split(',').map(term => term.trim());
      
      // Call each search term separately  
      let totalSuccess = 0;
      for (const productName of searchTermsArray) {
        try {
          const response = await fetch(`${API_BASE}/scraping/flipkart`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              platform: 'flipkart',
              product_name: productName
            }),
            credentials: 'include'
          });
          
          const result = await response.json();
          if (response.ok && result.total_products > 0) {
            totalSuccess++;
          }
        } catch (err) {
          console.error(`Flipkart scraping failed for ${productName}:`, err);
        }
      }
      
      if (totalSuccess > 0) {
        setScrapingStatus(prev => ({ ...prev, flipkart: 'success' }));
        setTimeout(() => {
          refetchSessions();
          fetchProducts();
        }, 2000);
      } else {
        setScrapingStatus(prev => ({ ...prev, flipkart: 'error' }));
      }
    } catch (error) {
      console.error('Flipkart scraping error:', error);
      setScrapingStatus(prev => ({ ...prev, flipkart: 'error' }));
    }
    
    setTimeout(() => {
      setScrapingStatus(prev => ({ ...prev, flipkart: '' }));
    }, 5000);
  };

  async function fetchProducts() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/products?limit=5`, {
        headers: getAuthHeaders(),
        credentials: 'include'
      });
      if (!res.ok) throw new Error(`Failed to load products: ${res.status}`);
      const data = await res.json();

      // Log raw response to DevTools so you can inspect exact fields if needed
      console.log("[/api/products] raw response:", data);

      const rawList: any[] = data.products ?? data.items ?? data.results ?? data.rows ?? [];
      if (!Array.isArray(rawList)) {
        console.warn("Unexpected /api/products payload, rawList is not array:", rawList);
      }

      const normalized = rawList.map(normalizeProductForYourDB);
      console.log("[/api/products] normalized sample:", normalized[0]);
      console.log("[/api/products] all normalized products:", normalized);
      setProducts(normalized);
    } catch (e: any) {
      console.error("fetchProducts error:", e);
      setError(e.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handlePredict(product: NormalizedProduct) {
    const pid = product.id ?? product.name;
    setPredictingId(pid ?? null);
    setPredictions((p) => ({ ...p, [pid]: { status: "running" } }));

    try {
      const result = await predictPrice(String(pid));
      
      if (result.success) {
        setPredictions((p) => ({ ...p, [pid]: { status: "done", output: result.data.prediction ?? result.data } }));
      } else {
        console.warn("LLM prediction failed, falling back to client-side heuristic:", result.error);
        const fallback = clientSidePredict(product);
        setPredictions((p) => ({ ...p, [pid]: { status: "done", output: { fallback: true, ...fallback } } }));
      }
    } catch (err) {
      console.error("predict error", err);
      const fallback = clientSidePredict(product);
      setPredictions((p) => ({ ...p, [pid]: { status: "done", output: { fallback: true, ...fallback } } }));
    } finally {
      setPredictingId(null);
    }
  }

  function clientSidePredict(product: NormalizedProduct) {
    try {
      const competitorPrices: number[] = [];
      Object.values(product.platforms || {}).forEach((p: any) => {
        if (p && typeof p.price === "number") competitorPrices.push(p.price);
      });

      const competitorAvg = competitorPrices.length ? competitorPrices.reduce((a, b) => a + b, 0) / competitorPrices.length : (product.pricing_summary.lowest_price ?? 0);
      const predicted = Math.round((competitorAvg || 0) * 0.98);

      const ourPrice = product.pricing_summary.lowest_price ?? 0;
      const decision = predicted && ourPrice ? (predicted < ourPrice ? "price_cut" : "hold") : "unknown";

      const llm_rationale = competitorPrices.length
        ? `Competitor average price is ₹${competitorAvg.toFixed(2)}. Suggested predicted price: ₹${predicted}.`
        : "Fallback heuristic used: insufficient competitor data.";

      return {
        predicted_price: predicted,
        competitor_average: Math.round(competitorAvg || 0),
        decision,
        llm_rationale,
        timestamp: new Date().toISOString(),
      };
    } catch (e) {
      return { error: "prediction failure" };
    }
  }

  return (
    <div className="space-y-6">
      {/* ✅ NEW: Scraper Control Panel */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-100 flex items-center gap-2">
            🤖 Scraper Control Panel
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Amazon Scraper */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-end">
            <div className="lg:col-span-2">
              <label className="text-sm text-gray-400 mb-2 block">Amazon Product Names (comma-separated)</label>
              <Input
                value={amazonSearchTerms}
                onChange={(e) => setAmazonSearchTerms(e.target.value)}
                placeholder="MacBook Pro, iPhone 15, Samsung Galaxy"
                className="bg-[#111214] border-gray-600 text-white"
              />
            </div>
            <Button
              onClick={handleAmazonScraping}
              disabled={scrapingStatus.amazon === 'running'}
              className={`
                ${scrapingStatus.amazon === 'running' ? 'bg-blue-600' : ''}
                ${scrapingStatus.amazon === 'success' ? 'bg-green-600' : ''}
                ${scrapingStatus.amazon === 'error' ? 'bg-red-600' : ''}
              `}
            >
              {scrapingStatus.amazon === 'running' && <InlineSpinner size={16} />}
              {scrapingStatus.amazon === 'running' ? 'Scraping Amazon...' : 
               scrapingStatus.amazon === 'success' ? '✅ Amazon Done' :
               scrapingStatus.amazon === 'error' ? '❌ Amazon Failed' : 
               'Trigger Amazon Scraper'}
            </Button>
          </div>

          {/* Smartprix Scraper */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-end">
            <div className="lg:col-span-2">
              <label className="text-sm text-gray-400 mb-2 block">Smartprix Product Names (comma-separated)</label>
              <Input
                value={smartprixSearchTerms}
                onChange={(e) => setSmartprixSearchTerms(e.target.value)}
                placeholder="MacBook Pro, iPhone 15, laptop"
                className="bg-[#111214] border-gray-600 text-white"
              />
            </div>
            <Button
              onClick={handleSmartprixScraping}
              disabled={scrapingStatus.smartprix === 'running'}
              className={`
                ${scrapingStatus.smartprix === 'running' ? 'bg-blue-600' : ''}
                ${scrapingStatus.smartprix === 'success' ? 'bg-green-600' : ''}
                ${scrapingStatus.smartprix === 'error' ? 'bg-red-600' : ''}
              `}
            >
              {scrapingStatus.smartprix === 'running' && <InlineSpinner size={16} />}
              {scrapingStatus.smartprix === 'running' ? 'Scraping Smartprix...' : 
               scrapingStatus.smartprix === 'success' ? '✅ Smartprix Done' :
               scrapingStatus.smartprix === 'error' ? '❌ Smartprix Failed' : 
               'Trigger Smartprix Scraper'}
            </Button>
          </div>

          {/* Flipkart Scraper */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-end">
            <div className="lg:col-span-2">
              <label className="text-sm text-gray-400 mb-2 block">Flipkart Product Names (comma-separated)</label>
              <Input
                value={flipkartSearchTerms}
                onChange={(e) => setFlipkartSearchTerms(e.target.value)}
                placeholder="MacBook Pro, iPhone 15, laptop"
                className="bg-[#111214] border-gray-600 text-white"
              />
            </div>
            <Button
              onClick={handleFlipkartScraping}
              disabled={scrapingStatus.flipkart === 'running'}
              className={`
                ${scrapingStatus.flipkart === 'running' ? 'bg-blue-600' : ''}
                ${scrapingStatus.flipkart === 'success' ? 'bg-green-600' : ''}
                ${scrapingStatus.flipkart === 'error' ? 'bg-red-600' : ''}
              `}
            >
              {scrapingStatus.flipkart === 'running' && <InlineSpinner size={16} />}
              {scrapingStatus.flipkart === 'running' ? 'Scraping Flipkart...' : 
               scrapingStatus.flipkart === 'success' ? '✅ Flipkart Done' :
               scrapingStatus.flipkart === 'error' ? '❌ Flipkart Failed' : 
               'Trigger Flipkart Scraper'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ✅ NEW: Recent Scraping Sessions */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-100 flex items-center justify-between">
            📊 Recent Scraping Sessions
            <Button onClick={refetchSessions} size="sm" variant="outline">
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <div className="flex items-center justify-center p-6">
              <InlineSpinner />
            </div>
          ) : sessions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-700">
                    <th className="py-2">Platform</th>
                    <th className="py-2">Scraped At</th>
                    <th className="py-2">Products</th>
                    <th className="py-2">Status</th>
                    <th className="py-2">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.slice(0, 10).map((session) => (
                    <tr key={session.id} className="border-b border-gray-800 hover:bg-[#111214]">
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium
                          ${session.platform === 'Amazon' ? 'bg-orange-900 text-orange-200' :
                            session.platform === 'Smartprix' ? 'bg-blue-900 text-blue-200' :
                            'bg-purple-900 text-purple-200'}
                        `}>
                          {session.platform}
                        </span>
                      </td>
                      <td className="py-3 text-gray-300">
                        {new Date(session.scraped_at).toLocaleString()}
                      </td>
                      <td className="py-3 text-white font-medium">
                        {session.total_products}
                      </td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium
                          ${session.success ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}
                        `}>
                          {session.success ? 'Success' : 'Failed'}
                        </span>
                      </td>
                      <td className="py-3 text-gray-400">
                        {session.execution_time ? `${session.execution_time}s` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              No scraping sessions found. Trigger a scraper above to get started!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Existing Products Table */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-100">Top 5 Products — Pricing & Predictions</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center p-6">
              <InlineSpinner />
            </div>
          ) : error ? (
            <div className="text-red-400">Error: {error}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full table-auto text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-700">
                    <th className="py-2">Product</th>
                    <th className="py-2">Our Price (₹)</th>
                    <th className="py-2">Competitor Price (₹)</th>
                    <th className="py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p) => {
                    // Debug logging
                    console.log('Product:', p.name);
                    console.log('Pricing summary:', p.pricing_summary);
                    console.log('Platforms:', p.platforms);
                    
                    // Use pricing summary for our price (lowest market price)
                    const ourPrice = typeof p.pricing_summary?.lowest_price === "number" ? p.pricing_summary.lowest_price : "—";
                    console.log('ourPrice:', ourPrice);
                    
                    // Use pricing summary for competitor price (highest market price)
                    const competitor = typeof p.pricing_summary?.highest_price === "number" ? p.pricing_summary.highest_price : "—";
                    console.log('competitor:', competitor);
                    
                    const key = p.id ?? p.name;
                    const pred = predictions[key];

                    return (
                      <React.Fragment key={key}>
                        <tr className="border-b border-gray-800 hover:bg-[#111214] transition-colors">
                          <td className="py-3 pr-4 align-top">
                            <div className="font-medium text-gray-100">{p.name}</div>
                            <div className="text-xs text-gray-400 mt-1">id: {p.id ?? "—"}</div>
                          </td>
                          <td className="py-3 align-top">{typeof ourPrice === "number" ? `₹${ourPrice}` : ourPrice}</td>
                          <td className="py-3 align-top">{typeof competitor === "number" ? `₹${competitor}` : competitor}</td>
                          <td className="py-3 align-top">
                            <div className="flex items-center gap-2">
                              <Button onClick={() => handlePredict(p)} disabled={predictingId === key}>
                                {predictingId === key ? "Predicting..." : "Predict"}
                              </Button>
                              <Button
                                variant="ghost"
                                onClick={() => {
                                  setPredictions((old) => ({ ...old, [key]: old[key] ? undefined : old[key] }));
                                }}
                              >
                                View
                              </Button>
                            </div>
                          </td>
                        </tr>

                        {/* Prediction Row */}
                        <tr>
                          <td colSpan={4} className="bg-[#121215] px-4 py-3">
                            {pred ? (
                              pred.status === "running" ? (
                                <div className="flex items-center gap-3">
                                  <InlineSpinner />
                                  <span className="text-gray-300">Running prediction...</span>
                                </div>
                              ) : (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                  <div>
                                    <div className="text-xs text-gray-400">Predicted Price</div>
                                    <div className="text-lg font-semibold text-white">₹{pred.output?.predicted_price ?? "—"}</div>
                                  </div>

                                  <div>
                                    <div className="text-xs text-gray-400">Decision</div>
                                    <div className={`text-sm font-medium ${pred.output?.decision === "price_cut" ? "text-rose-400" : "text-green-400"}`}>
                                      {pred.output?.decision ?? "—"}
                                    </div>
                                  </div>

                                  <div className="md:col-span-1">
                                    <div className="text-xs text-gray-400">LLM Rationale</div>
                                    <div className="text-sm text-gray-200 mt-1 whitespace-pre-wrap">
                                      {pred.output?.llm_rationale ?? JSON.stringify(pred.output ?? {})}
                                    </div>
                                  </div>
                                </div>
                              )
                            ) : (
                              <div className="text-xs text-gray-500">No prediction run yet. Click "Predict" to generate ML + LLM output for this product.</div>
                            )}
                          </td>
                        </tr>
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ✅ NEW: Comprehensive Scraping Results & Analytics */}
      <ScrapingResultsAnalytics />
    </div>
  );
}