import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

// API Configuration
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ScrapingSession {
  id: string;
  session_id: string;
  scraped_at: string;
  platform: string;
  total_products: number;
  search_query: string;
  success: boolean;
  execution_time: number;
  errors: number;
  products: Array<{
    title: string;
    price: string;
    original_price?: string;
    url: string;
    rating?: string;
    reviews?: string;
    image?: string;
    availability?: string;
    specifications?: Record<string, any>;
    features?: string[];
  }>;
}

interface ScrapingResultsAnalyticsProps {
  className?: string;
}

export default function ScrapingResultsAnalytics({ className }: ScrapingResultsAnalyticsProps) {
  const [sessions, setSessions] = useState<ScrapingSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  const fetchScrapingSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use direct connection to backend since proxy seems to not be working
      const apiUrl = `${API_BASE}/api/scraping/recent-sessions`;
      console.log('Fetching scraping sessions from:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });
      
      console.log('Response status:', response.status);
      console.log('Response content-type:', response.headers.get('content-type'));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Received data:', data);
      
      if (data.success) {
        setSessions(data.sessions || []);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch scraping sessions');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Network error while fetching scraping sessions';
      setError(errorMessage);
      console.error('Error fetching scraping sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScrapingSessions();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchScrapingSessions, 30000);
    return () => clearInterval(interval);
  }, []);

  // Analytics calculations
  const analytics = React.useMemo(() => {
    if (!sessions.length) return null;

    const platformStats = sessions.reduce((acc, session) => {
      const platform = session.platform.toLowerCase();
      if (!acc[platform]) {
        acc[platform] = { 
          sessions: 0, 
          totalProducts: 0, 
          successRate: 0, 
          avgDuration: 0,
          lastRun: null as Date | null
        };
      }
      
      acc[platform].sessions += 1;
      acc[platform].totalProducts += session.total_products;
      
      const sessionDate = new Date(session.scraped_at);
      if (!acc[platform].lastRun || sessionDate > acc[platform].lastRun) {
        acc[platform].lastRun = sessionDate;
      }
      
      return acc;
    }, {} as Record<string, any>);

    // Calculate success rates and average durations
    Object.keys(platformStats).forEach(platform => {
      const platformSessions = sessions.filter(s => s.platform.toLowerCase() === platform);
      const successfulSessions = platformSessions.filter(s => s.success);
      platformStats[platform].successRate = (successfulSessions.length / platformSessions.length) * 100;
      
      const durationsWithData = platformSessions.filter(s => s.execution_time > 0);
      platformStats[platform].avgDuration = durationsWithData.length > 0 
        ? durationsWithData.reduce((sum, s) => sum + s.execution_time, 0) / durationsWithData.length
        : 0;
    });

    return {
      totalSessions: sessions.length,
      totalProducts: sessions.reduce((sum, s) => sum + s.total_products, 0),
      platforms: platformStats,
      recentSessions: sessions.slice(0, 5)
    };
  }, [sessions]);

  const filteredSessions = selectedPlatform 
    ? sessions.filter(s => s.platform.toLowerCase() === selectedPlatform.toLowerCase())
    : sessions;

  const selectedSessionData = selectedSession 
    ? sessions.find(s => s.id === selectedSession) 
    : null;

  if (loading) {
    return (
      <Card className={`bg-[#1b1b1f] border border-gray-700 ${className}`}>
        <CardContent className="flex items-center justify-center p-8">
          <div className="text-gray-400">Loading scraping results...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`bg-red-900/20 border border-red-800 ${className}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-400 font-medium">Failed to load scraping results</p>
              <p className="text-red-300 text-sm mt-1">{error}</p>
              <p className="text-gray-400 text-xs mt-2">
                Trying to connect to: {API_BASE}/api/scraping/recent-sessions
              </p>
            </div>
            <div className="flex flex-col gap-2">
              <Button onClick={fetchScrapingSessions} className="bg-red-600 hover:bg-red-700">
                Retry
              </Button>
              <Button 
                onClick={async () => {
                  try {
                    const response = await fetch(`${API_BASE}/api/products`);
                    const data = await response.json();
                    console.log('Products API test:', data);
                    alert('Connection test successful! Backend is working.');
                  } catch (err) {
                    console.error('Connection test failed:', err);
                    alert(`Connection test failed: ${err}. Make sure backend is running on port 8000.`);
                  }
                }}
                size="sm"
                variant="outline"
                className="text-xs"
              >
                Test Connection
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analytics) {
    return (
      <Card className={`bg-[#1b1b1f] border border-gray-700 ${className}`}>
        <CardHeader>
          <CardTitle className="text-gray-100">📊 Scraping Results & Analytics</CardTitle>
        </CardHeader>
        <CardContent className="text-center text-gray-400 py-8">
          No scraping data available yet. Run some scrapers to see results here!
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-[#1b1b1f] border border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-400">Total Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{analytics.totalSessions}</div>
            <p className="text-xs text-green-400 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card className="bg-[#1b1b1f] border border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-400">Products Scraped</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{analytics.totalProducts.toLocaleString()}</div>
            <p className="text-xs text-blue-400 mt-1">Across all platforms</p>
          </CardContent>
        </Card>

        <Card className="bg-[#1b1b1f] border border-gray-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-400">Active Platforms</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{Object.keys(analytics.platforms).length}</div>
            <p className="text-xs text-purple-400 mt-1">Amazon, Smartprix, Flipkart</p>
          </CardContent>
        </Card>
      </div>

      {/* Session Details Table */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-gray-100">
              📋 Recent Scraping Sessions {selectedPlatform && `- ${selectedPlatform}`}
            </CardTitle>
            <div className="flex items-center gap-2">
              {selectedPlatform && (
                <Button 
                  onClick={() => setSelectedPlatform(null)} 
                  size="sm" 
                  variant="ghost"
                  className="text-gray-400"
                >
                  Clear Filter
                </Button>
              )}
              <Button onClick={fetchScrapingSessions} size="sm" variant="outline">
                Refresh
              </Button>
              <Badge variant="outline" className="text-gray-400">
                {filteredSessions.length} sessions
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredSessions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-700">
                    <th className="py-3 px-2">Platform</th>
                    <th className="py-3 px-2">Timestamp</th>
                    <th className="py-3 px-2">Search Query</th>
                    <th className="py-3 px-2">Products</th>
                    <th className="py-3 px-2">Status</th>
                    <th className="py-3 px-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSessions.map((session) => (
                    <tr 
                      key={session.id} 
                      className={`border-b border-gray-800 hover:bg-[#111214] transition-colors
                        ${selectedSession === session.id ? 'bg-blue-900/20' : ''}
                      `}
                    >
                      <td className="py-3 px-2">
                        <Badge 
                          className={`cursor-pointer
                            ${session.platform === 'Amazon' ? 'bg-orange-900 text-orange-200 hover:bg-orange-800' :
                              session.platform === 'Smartprix' ? 'bg-blue-900 text-blue-200 hover:bg-blue-800' :
                              'bg-purple-900 text-purple-200 hover:bg-purple-800'}
                          `}
                          onClick={() => setSelectedPlatform(
                            selectedPlatform === session.platform ? null : session.platform
                          )}
                        >
                          {session.platform}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-gray-300">
                        {new Date(session.scraped_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-2 text-gray-400 max-w-xs truncate">
                        {session.search_query}
                      </td>
                      <td className="py-3 px-2">
                        <span className={`font-medium ${session.total_products > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {session.total_products}
                        </span>
                      </td>
                      <td className="py-3 px-2">
                        <Badge 
                          className={session.success 
                            ? 'bg-green-900 text-green-200' 
                            : 'bg-red-900 text-red-200'
                          }
                        >
                          {session.success ? '✅ Success' : '❌ Failed'}
                        </Badge>
                      </td>
                      <td className="py-3 px-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setSelectedSession(
                            selectedSession === session.id ? null : session.id
                          )}
                          className="text-xs"
                        >
                          {selectedSession === session.id ? 'Hide Products' : 'View Products'}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              No sessions found for the selected filter.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scraped Products Details */}
      {selectedSessionData && (
        <Card className="bg-[#0f1014] border border-blue-700">
          <CardHeader>
            <CardTitle className="text-blue-400 flex items-center justify-between">
              🛍️ Scraped Products from {selectedSessionData.platform} - {selectedSessionData.search_query}
              <Button 
                onClick={() => setSelectedSession(null)} 
                size="sm" 
                variant="ghost"
                className="text-gray-400"
              >
                ✕
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedSessionData.products.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                {selectedSessionData.products.map((product, index) => (
                  <div key={index} className="bg-[#1a1a1a] p-4 rounded-lg border border-gray-700">
                    <div className="space-y-2">
                      <h4 className="font-medium text-white text-sm line-clamp-2">
                        {product.title}
                      </h4>
                      
                      <div className="flex items-center gap-2">
                        <span className="text-green-400 font-bold">
                          {product.price}
                        </span>
                        {product.original_price && product.original_price !== product.price && (
                          <span className="text-gray-500 line-through text-xs">
                            {product.original_price}
                          </span>
                        )}
                      </div>

                      {product.rating && (
                        <div className="flex items-center gap-1">
                          <span className="text-yellow-400">⭐</span>
                          <span className="text-gray-300 text-xs">{product.rating}</span>
                          {product.reviews && (
                            <span className="text-gray-500 text-xs">({product.reviews})</span>
                          )}
                        </div>
                      )}

                      {product.availability && (
                        <span className={`text-xs px-2 py-1 rounded ${
                          product.availability.toLowerCase().includes('stock') 
                            ? 'bg-green-900 text-green-200' 
                            : 'bg-yellow-900 text-yellow-200'
                        }`}>
                          {product.availability}
                        </span>
                      )}

                      {product.url && (
                        <a 
                          href={product.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 text-xs underline block truncate"
                        >
                          View Product →
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                No products found in this session.
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}