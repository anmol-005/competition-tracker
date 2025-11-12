import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import UserManagement from "@/pages/UserManagement";
import ProductScraperManagement from "@/pages/ProductScraperManagement";
import MLLlmManagement from "@/pages/MLLlmManagement";
import SubscriptionsBilling from "@/pages/SubscriptionsBilling";
import AdminSettings from "@/pages/AdminSettings";

// ✅ NEW: Import the admin API hook for real database data
import { useAdminDashboard } from "@/hooks/use-admin-api";

// ✅ NEW: Import scraping results analytics component
import ScrapingResultsAnalytics from "@/components/ScrapingResultsAnalytics";

import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  ResponsiveContainer,
} from "recharts";

import {
  LayoutDashboard,
  Users,
  ShoppingBag,
  Brain,
  CreditCard,
  Settings,
  Activity,
  Circle,
  LogOut,
} from "lucide-react";

export default function AdminDashboard() {
  const [activePage, setActivePage] = useState("Dashboard");

  
  const { dashboardData, loading, error, refetch } = useAdminDashboard();

  
  const stats = dashboardData?.stats || {
    total_products: 0,
    total_users: 0,
    platforms: { amazon: 0, smartprix: 0, flipkart: 0 },
    recent_activity: { products_updated_today: 0, scraping_sessions_today: 0 }
  };

  const revenueData = dashboardData?.revenue_trends || [];

  const topProducts = dashboardData?.top_products || [];

  const recentActivity = dashboardData?.recent_activity || [];

  const sidebarItems = [
    { label: "Dashboard", icon: LayoutDashboard },
    { label: "User Management", icon: Users },
    { label: "Product & Scraper Management", icon: ShoppingBag },
    { label: "ML & LLM Management", icon: Brain },
    { label: "Subscriptions & Billing", icon: CreditCard },
    { label: "Settings", icon: Settings },
  ];

  // --- Logout handler
  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  // --- Page mapping
  const pages: Record<string, JSX.Element> = {
    "Dashboard": (
      <>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard Overview</h1>
          
          {/* ✅ NEW: Data source indicator */}
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${error ? 'bg-red-400' : 'bg-green-400'}`}></div>
            <span className="text-sm text-gray-400">
              {error ? 'Offline Mode' : 'Live Database'}
            </span>
            {!loading && (
              <Button 
                onClick={refetch} 
                size="sm" 
                variant="ghost" 
                className="h-6 w-6 p-0"
              >
                🔄
              </Button>
            )}
          </div>
        </div>

        {/* ✅ UPDATED: KPI Cards with real database data */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Total Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-3xl font-bold text-gray-500">Loading...</p>
              ) : (
                <>
                  <p className="text-3xl font-bold text-white">{stats.total_users.toLocaleString()}</p>
                  <p className="text-xs text-green-400 mt-1">MongoDB Live Data</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Total Products Tracked</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-3xl font-bold text-gray-500">Loading...</p>
              ) : (
                <>
                  <p className="text-3xl font-bold text-white">{stats.total_products.toLocaleString()}</p>
                  <p className="text-xs text-blue-400 mt-1">
                    Amazon: {stats.platforms.amazon} | Smartprix: {stats.platforms.smartprix} | Flipkart: {stats.platforms.flipkart}
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Scraping Sessions Today</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-3xl font-bold text-gray-500">Loading...</p>
              ) : (
                <>
                  <p className="text-3xl font-bold text-white">{stats.recent_activity.scraping_sessions_today}</p>
                  <p className="text-xs text-green-400 mt-1">
                    Products Updated: {stats.recent_activity.products_updated_today}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* ✅ NEW: Error handling and refresh button */}
        {error && (
          <Card className="bg-red-900/20 border-red-800">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-400 font-medium">Database Connection Issue</p>
                  <p className="text-red-300 text-sm mt-1">{error}</p>
                </div>
                <Button 
                  onClick={refetch}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle>Revenue Growth Trend (Last 6 Months)</CardTitle>
            </CardHeader>
            <CardContent className="h-64">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                  <p className="mt-2 text-sm">Loading revenue data...</p>
                </div>
              ) : revenueData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="month" stroke="#888" />
                    <YAxis stroke="#888" />
                    <Tooltip contentStyle={{ backgroundColor: "#1c1c1e", border: "none" }} />
                    <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <div className="text-4xl mb-3">📊</div>
                  <p className="text-lg font-medium">No revenue data available</p>
                  <p className="text-sm mt-1">Revenue trends will appear as data is collected</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle>Top 5 Most Tracked Products</CardTitle>
            </CardHeader>
            <CardContent className="h-64">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
                  <p className="mt-2 text-sm">Loading product data...</p>
                </div>
              ) : topProducts.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topProducts}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="name" stroke="#888" />
                    <YAxis stroke="#888" />
                    <Tooltip contentStyle={{ backgroundColor: "#1c1c1e", border: "none" }} />
                    <Bar dataKey="scrapes" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <div className="text-4xl mb-3">🏆</div>
                  <p className="text-lg font-medium">No product tracking data</p>
                  <p className="text-sm mt-1">Start scraping products to see top tracked items</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* System Health */}
        <Card className="bg-[#18181b] border border-gray-700">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              🩺 System Health
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { name: "Amazon Scraper", status: "Healthy", color: "text-green-400" },
              { name: "Smartprix Scraper", status: "Healthy", color: "text-green-400" },
              { name: "Classification Model", status: "Healthy", color: "text-green-400" },
            ].map((s) => (
              <div
                key={s.name}
                className="flex items-center justify-between bg-[#1e1e21] p-4 rounded-xl border border-gray-700 shadow-sm hover:bg-[#222225] transition-all"
              >
                <span className="text-gray-200 font-medium">{s.name}</span>
                <span className={`flex items-center gap-1 ${s.color} text-sm font-semibold`}>
                  <Circle className="h-3 w-3 fill-green-400 text-green-400" /> {s.status}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="bg-[#18181b] border-gray-800">
          <CardHeader className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-400" />
              <CardTitle className="text-lg font-semibold text-gray-100">Recent Activity</CardTitle>
            </div>
          </CardHeader>

          <CardContent className="divide-y divide-gray-800">
            {loading ? (
              <div className="py-6 text-center text-gray-400">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
                <p className="mt-2 text-sm">Loading recent activity...</p>
              </div>
            ) : recentActivity.length > 0 ? (
              recentActivity.map((a, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-3 hover:bg-[#1f1f22] transition-colors rounded-md px-2"
                >
                  <div className="flex items-center gap-2 text-gray-200">
                    {a.type === "signup" ? (
                      <>
                        <span className="text-yellow-400">🧍</span>
                        <span>
                          <span className="text-gray-300">New user</span>{" "}
                          <span className="font-medium text-white">{a.user}</span>{" "}
                          <span className="text-gray-400">signed up</span>
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="text-blue-400">⚙️</span>
                        <span className="text-gray-300">{a.message}</span>
                      </>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">{a.time}</span>
                </div>
              ))
            ) : (
              <div className="py-6 text-center text-gray-400">
                <Activity className="h-12 w-12 mx-auto mb-3 text-gray-600" />
                <p className="text-lg font-medium">No recent activity</p>
                <p className="text-sm mt-1">Activity will appear here once users start using the system</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ✅ NEW: Scraping Results & Analytics */}
        <ScrapingResultsAnalytics />
      </>
    ),
    "User Management": <UserManagement />,
    "Product & Scraper Management": <ProductScraperManagement />,
    "ML & LLM Management": <MLLlmManagement />,
    "Subscriptions & Billing": <SubscriptionsBilling />,
    "Settings": <AdminSettings />,
  };

  return (
    <div className="flex min-h-screen bg-[#0f0f11] text-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-[#121214] border-r border-gray-800 flex flex-col">
        <div className="p-6 text-xl font-bold text-primary tracking-wide">🧠 CompIntel</div>

        <nav className="flex-1 space-y-1 px-4">
          {sidebarItems.map(({ label, icon: Icon }) => (
            <Button
              key={label}
              variant={activePage === label ? "secondary" : "ghost"}
              className={`w-full justify-start gap-2 text-sm ${
                activePage === label ? "bg-primary/10 text-primary" : "text-gray-400"
              }`}
              onClick={() => setActivePage(label)}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Button>
          ))}
        </nav>

        {/* ✅ Logout button */}
        <div className="p-4 border-t border-gray-800">
          <Button
            onClick={handleLogout}
            className="w-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>

        <div className="p-4 text-xs text-gray-500 border-t border-gray-800">
          © 2025 CompIntel
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 space-y-6 overflow-y-auto">{pages[activePage]}</main>
    </div>
  );
}
