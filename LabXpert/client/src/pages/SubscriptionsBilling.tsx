import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function SubscriptionsBilling() {
  const plans = [
    { user: "jane_doe", plan: "Pro", amount: "$29.99", renewal: "Dec 10, 2025" },
    { user: "mark_analytics", plan: "Starter", amount: "$9.99", renewal: "Nov 21, 2025" },
  ];

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold text-gray-100">Subscriptions & Billing</h1>

      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">Active Subscriptions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {plans.map((p, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 bg-[#222226] rounded-lg border border-gray-700 hover:bg-[#26262a] transition-all"
            >
              <div>
                <p className="text-gray-100 font-medium">{p.user}</p>
                <p className="text-xs text-gray-400">Renewal: {p.renewal}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-blue-400 text-sm font-semibold">{p.plan}</span>
                <span className="text-gray-300 text-sm">{p.amount}</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">Payment History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400 text-sm">No payments yet.</p>
        </CardContent>
      </Card>
    </div>
  );
}
