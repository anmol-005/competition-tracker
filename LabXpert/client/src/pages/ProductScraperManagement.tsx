import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function ProductScraperManagement() {
  const scrapers = [
    { name: "Amazon Scraper", status: "Healthy", color: "text-green-400", lastRun: "10 min ago" },
    { name: "Smartprix Scraper", status: "Healthy", color: "text-green-400", lastRun: "25 min ago" },
    { name: "Flipkart Scraper", status: "Idle", color: "text-yellow-400", lastRun: "1 hr ago" },
  ];

  const topProducts = [
    { name: "MacBook Air M2", scrapes: 1280 },
    { name: "iPhone 15 Pro", scrapes: 1040 },
    { name: "Dell XPS 13", scrapes: 860 },
  ];

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold text-gray-100">Product & Scraper Management</h1>

      {/* Active Scrapers */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">Active Scrapers</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {scrapers.map((s, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 bg-[#222226] rounded-lg border border-gray-700"
            >
              <div>
                <p className="text-gray-100 font-medium">{s.name}</p>
                <p className="text-xs text-gray-400">Last Run: {s.lastRun}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${s.color} bg-opacity-10`}>
                {s.status}
              </span>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Top Products */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">Top Tracked Products</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {topProducts.map((p, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 bg-[#222226] rounded-lg border border-gray-700"
            >
              <span className="text-gray-100">{p.name}</span>
              <span className="text-blue-400 font-medium">{p.scrapes} scrapes</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
