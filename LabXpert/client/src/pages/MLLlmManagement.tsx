import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function MLLlmManagement() {
  const models = [
    { name: "Classification Model", version: "v1.3", status: "Healthy" },
    { name: "Price Predictor", version: "v2.0", status: "Training" },
    { name: "Review Sentiment Analyzer", version: "v1.1", status: "Healthy" },
  ];

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold text-gray-100">ML & LLM Management</h1>

      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">Deployed Models</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {models.map((m, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 bg-[#222226] rounded-lg border border-gray-700 hover:bg-[#26262a] transition-all"
            >
              <div>
                <p className="text-gray-100 font-medium">{m.name}</p>
                <p className="text-xs text-gray-400">Version: {m.version}</p>
              </div>
              <span
                className={`px-3 py-1 text-xs font-semibold rounded-full ${
                  m.status === "Healthy"
                    ? "text-green-400 bg-green-400/10"
                    : "text-yellow-400 bg-yellow-400/10"
                }`}
              >
                {m.status}
              </span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
