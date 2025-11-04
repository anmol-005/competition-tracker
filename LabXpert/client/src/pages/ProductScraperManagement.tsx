// client/src/pages/ProductScraperManagement.tsx
import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";

/**
 * Complete ProductScraperManagement.tsx
 *
 * - Overwrite your existing file with this.
 * - Relative imports (no "@/..." alias).
 * - Inline spinner so you do not need a separate spinner file.
 * - Normalizes your DB response shape (ASIN, Model_Name, etc.)
 * - Calls POST /api/predict/{productId} and falls back to a client-side heuristic
 */

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
type PlatformInfo = {
  price?: number | null;
  url?: string | null;
};

type NormalizedProduct = {
  id: string | null;
  name: string;
  platforms: Record<string, PlatformInfo>;
  pricing_summary: {
    lowest_price?: number | null;
    highest_price?: number | null;
    best_platform?: string | null;
  };
  _raw?: any;
};

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

  // Collect many candidate price fields
  const priceCandidates: (number | null)[] = [
    safeNumber(raw.price ?? raw.Price ?? raw.current_price ?? raw.our_price ?? raw.OurPrice ?? null),
    safeNumber(raw.MRP ?? raw.mrp ?? raw.list_price ?? raw.ListPrice ?? null),
    safeNumber(raw.BuyBox_Price ?? raw.buybox_price ?? raw.buy_box_price ?? null),
    safeNumber(raw.min_price ?? raw.minPrice ?? null),
    safeNumber(raw.max_price ?? raw.maxPrice ?? null),
  ];

  // offers array (if present)
  if (Array.isArray(raw.offers)) {
    raw.offers.forEach((o: any) => {
      priceCandidates.push(safeNumber(o.price ?? o.Price ?? o.offer_price ?? o.amount ?? null));
    });
  }

  // marketplaces array
  if (Array.isArray(raw.marketplaces)) {
    raw.marketplaces.forEach((m: any) => {
      priceCandidates.push(safeNumber(m.price ?? m.amount ?? null));
    });
  }

  // competitors map
  if (raw.competitors && typeof raw.competitors === "object") {
    Object.values(raw.competitors).forEach((c: any) => {
      priceCandidates.push(safeNumber(c?.price ?? c?.amount ?? null));
    });
  }

  // Flatten numeric candidates
  const numeric = priceCandidates.filter((x) => typeof x === "number") as number[];
  const lowest_price = numeric.length ? Math.min(...numeric) : null;
  const highest_price = numeric.length ? Math.max(...numeric) : null;

  // Build platforms map: try raw.platforms, else create our_store + competitors/offers
  const platforms: Record<string, PlatformInfo> = {};
  if (raw.platforms && typeof raw.platforms === "object") {
    Object.entries(raw.platforms).forEach(([k, v]: any) => {
      platforms[k] = { price: safeNumber(v?.price ?? v?.current_price ?? v?.amount), url: v?.url ?? v?.link ?? null };
    });
  } else if (raw.competitors && typeof raw.competitors === "object") {
    Object.entries(raw.competitors).forEach(([k, v]: any) => {
      platforms[k] = { price: safeNumber(v?.price ?? v?.amount), url: v?.url ?? null };
    });
    // ensure our_store exists
    platforms["our_store"] = platforms["our_store"] ?? { price: safeNumber(raw.our_price ?? raw.price ?? lowest_price), url: raw.url ?? null };
  } else if (Array.isArray(raw.offers) && raw.offers.length) {
    raw.offers.forEach((o: any, i: number) => {
      const pname = o.platform ?? o.seller ?? `offer_${i}`;
      platforms[pname] = { price: safeNumber(o.price ?? o.offer_price ?? o.amount), url: o.url ?? o.link ?? null };
    });
    platforms["our_store"] = platforms["our_store"] ?? { price: safeNumber(raw.our_price ?? raw.price ?? lowest_price), url: raw.url ?? null };
  } else {
    // fallback single entries
    platforms["our_store"] = { price: safeNumber(raw.our_price ?? raw.price ?? lowest_price), url: raw.url ?? null };
    const compPrice = safeNumber(raw.competitor_price ?? raw.CompetitorPrice ?? highest_price);
    if (compPrice) platforms["competitor_a"] = { price: compPrice, url: raw.competitor_url ?? null };
  }

  const pricing_summary = {
    lowest_price,
    highest_price,
    best_platform: raw.best_platform ?? raw.BEST_PLATFORM ?? raw.pricing_summary?.best_platform ?? null,
  };

  return { id, name, platforms, pricing_summary, _raw: raw };
}

/* ---------- Component ---------- */
export default function ProductScraperManagement(): JSX.Element {
  const [products, setProducts] = useState<NormalizedProduct[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [predictingId, setPredictingId] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchProducts() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/products?limit=5`);
      if (!res.ok) throw new Error(`Failed to load products: ${res.status}`);
      const data = await res.json();

      // Log raw response to DevTools so you can inspect exact fields if needed
      // (remove this later if you want)
      // eslint-disable-next-line no-console
      console.log("[/api/products] raw response:", data);

      const rawList: any[] = data.products ?? data.items ?? data.results ?? data.rows ?? [];
      if (!Array.isArray(rawList)) {
        console.warn("Unexpected /api/products payload, rawList is not array:", rawList);
      }

      const normalized = rawList.map(normalizeProductForYourDB);
      // eslint-disable-next-line no-console
      console.log("[/api/products] normalized sample:", normalized[0]);
      setProducts(normalized);
    } catch (e: any) {
      // eslint-disable-next-line no-console
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
      const res = await fetch(`/api/predict/${encodeURIComponent(String(pid))}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product }),
      });

      if (res.ok) {
        const payload = await res.json();
        // support both { prediction: {...} } and direct payload
        setPredictions((p) => ({ ...p, [pid]: { status: "done", output: payload.prediction ?? payload } }));
      } else {
        // fallback to client-side prediction
        // eslint-disable-next-line no-console
        console.warn("/api/predict failed, falling back to client-side heuristic");
        const fallback = clientSidePredict(product);
        setPredictions((p) => ({ ...p, [pid]: { status: "done", output: { fallback: true, ...fallback } } }));
      }
    } catch (err) {
      // eslint-disable-next-line no-console
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
                  const ourPrice = p.pricing_summary?.lowest_price ?? "—";
                  const competitor = p.pricing_summary?.highest_price ?? "—";
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
  );
}
