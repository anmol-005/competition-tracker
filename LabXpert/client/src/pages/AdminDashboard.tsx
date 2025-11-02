import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import UserManagement from "@/pages/UserManagement";
import ProductScraperManagement from "@/pages/ProductScraperManagement";
import MLLlmManagement from "@/pages/MLLlmManagement";
import SubscriptionsBilling from "@/pages/SubscriptionsBilling";
import AdminSettings from "@/pages/AdminSettings";

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

  // --- Static data (placeholders until DB integration)
  const revenueData = [
    { month: "Jun", revenue: 15000 },
    { month: "Jul", revenue: 22000 },
    { month: "Aug", revenue: 27000 },
    { month: "Sep", revenue: 34000 },
    { month: "Oct", revenue: 42000 },
    { month: "Nov", revenue: 48000 },
  ];

  const topProducts = [
    { name: "MacBook Air M2", scrapes: 1200 },
    { name: "iPhone 15 Pro", scrapes: 980 },
    { name: "Dell XPS 13", scrapes: 850 },
    { name: "Asus ROG Zephyrus", scrapes: 790 },
    { name: "Lenovo Legion 7", scrapes: 670 },
  ];

  const recentActivity = [
    { type: "signup", user: "jane_doe", time: "2m ago" },
    { type: "scraper", message: "Amazon Scraper executed successfully", time: "10m ago" },
    { type: "signup", user: "mark_analytics", time: "25m ago" },
    { type: "scraper", message: "Smartprix Scraper completed 500 items", time: "1h ago" },
  ];

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
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard Overview</h1>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Total Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">1,248</p>
              <p className="text-xs text-green-400 mt-1">+5.4% this week</p>
            </CardContent>
          </Card>

          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Monthly Recurring Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">$48,000</p>
              <p className="text-xs text-green-400 mt-1">+12.2% from last month</p>
            </CardContent>
          </Card>

          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Total Scrapes Executed Today</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">7,893</p>
              <p className="text-xs text-green-400 mt-1">+3.1% vs yesterday</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle>Revenue Growth Trend (Last 6 Months)</CardTitle>
            </CardHeader>
            <CardContent className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                  <XAxis dataKey="month" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip contentStyle={{ backgroundColor: "#1c1c1e", border: "none" }} />
                  <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-[#18181b] border-gray-800">
            <CardHeader>
              <CardTitle>Top 5 Most Tracked Products</CardTitle>
            </CardHeader>
            <CardContent className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topProducts}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                  <XAxis dataKey="name" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip contentStyle={{ backgroundColor: "#1c1c1e", border: "none" }} />
                  <Bar dataKey="scrapes" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
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
            {recentActivity.map((a, i) => (
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
            ))}
          </CardContent>
        </Card>
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
