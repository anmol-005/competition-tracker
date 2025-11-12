import { useState, useEffect } from 'react';

// API base URL - adjust based on your FastAPI server
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface DashboardStats {
  total_products: number;
  total_users: number;
  platforms: {
    amazon: number;
    smartprix: number;
    flipkart: number;
  };
  recent_activity: {
    products_updated_today: number;
    scraping_sessions_today: number;
  };
}

interface RevenueData {
  month: string;
  revenue: number;
}

interface TopProduct {
  name: string;
  scrapes: number;
}

interface RecentActivity {
  type: string;
  user?: string;
  message?: string;
  time: string;
}

interface DashboardResponse {
  success: boolean;
  stats: DashboardStats;
  revenue_trends: RevenueData[];
  top_products: TopProduct[];
  recent_activity: RecentActivity[];
}

interface ScrapingSession {
  id: string;
  platform: string;
  scraped_at: string;
  total_products: number;
  success: boolean;
  errors: number;
  execution_time: number;
}

interface User {
  _id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  flagged?: boolean;
  created_at: string;
}

// Helper function to get auth token
const getAuthToken = (): string | null => {
  // Try to get token from different possible storage locations
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  if (token) {
    return token;
  }
  
  // Fallback: check user object for token
  const user = localStorage.getItem('user');
  if (user) {
    try {
      const userData = JSON.parse(user);
      return userData.access_token || userData.token;
    } catch {
      return null;
    }
  }
  
  // Check if authenticated user exists (for session-based auth)
  const isAuthenticated = localStorage.getItem('isAuthenticated');
  if (isAuthenticated === 'true') {
    // For session-based auth, we might not need to send a token
    return 'session-auth';
  }
  
  return null;
};

// Helper function to make authenticated API calls
const makeAuthenticatedRequest = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  
  if (token && token !== 'session-auth') {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Include cookies for session-based auth
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
};

// Custom hook for dashboard stats
export const useAdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await makeAuthenticatedRequest('/admin/dashboard-stats');
      setDashboardData(data);
    } catch (err) {
      console.error('❌ Error fetching dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
      
      // Keep dashboardData as null to show loading state instead of demo data
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return { dashboardData, loading, error, refetch: fetchDashboardData };
};

// Custom hook for scraping sessions
export const useScrapingSessions = () => {
  const [sessions, setSessions] = useState<ScrapingSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await makeAuthenticatedRequest('/admin/scraping-sessions');
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('❌ Error fetching scraping sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch scraping sessions');
      
      // Keep sessions empty to show loading state instead of demo data
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return { sessions, loading, error, refetch: fetchSessions };
};

// Custom hook for user management
export const useAdminUsers = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await makeAuthenticatedRequest('/admin/users');
      setUsers(data.users || []);
    } catch (err) {
      console.error('❌ Error fetching users:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
      
      // Keep users empty to show loading state instead of demo data
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const flagUser = async (userId: string) => {
    try {
      await makeAuthenticatedRequest(`/admin/users/${userId}/flag`, {
        method: 'POST'
      });
      await fetchUsers(); // Refresh the list
      return { success: true };
    } catch (err) {
      console.error('❌ Error flagging user:', err);
      return { success: false, error: err instanceof Error ? err.message : 'Failed to flag user' };
    }
  };

  const banUser = async (userId: string) => {
    try {
      await makeAuthenticatedRequest(`/admin/users/${userId}/ban`, {
        method: 'POST'
      });
      await fetchUsers(); // Refresh the list
      return { success: true };
    } catch (err) {
      console.error('❌ Error banning user:', err);
      return { success: false, error: err instanceof Error ? err.message : 'Failed to ban user' };
    }
  };

  const unbanUser = async (userId: string) => {
    try {
      await makeAuthenticatedRequest(`/admin/users/${userId}/unban`, {
        method: 'POST'
      });
      await fetchUsers(); // Refresh the list
      return { success: true };
    } catch (err) {
      console.error('❌ Error unbanning user:', err);
      return { success: false, error: err instanceof Error ? err.message : 'Failed to unban user' };
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return { users, loading, error, refetch: fetchUsers, flagUser, banUser, unbanUser };
};

// Function to trigger scraping manually
export const triggerScraping = async (platform: string, params: any) => {
  try {
    const endpoint = `/scraping/${platform.toLowerCase()}`;
    const result = await makeAuthenticatedRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(params)
    });
    return { success: true, data: result };
  } catch (err) {
    console.error(`❌ Error triggering ${platform} scraping:`, err);
    return { 
      success: false, 
      error: err instanceof Error ? err.message : `Failed to trigger ${platform} scraping` 
    };
  }
};

// Function to predict price using LLM
export const predictPrice = async (productId: string) => {
  try {
    const result = await makeAuthenticatedRequest(`/predict/${productId}`, {
      method: 'POST'
    });
    return { success: true, data: result };
  } catch (err) {
    console.error(`❌ Error predicting price for product ${productId}:`, err);
    return { 
      success: false, 
      error: err instanceof Error ? err.message : `Failed to predict price` 
    };
  }
};

export default {
  useAdminDashboard,
  useScrapingSessions,
  useAdminUsers,
  triggerScraping,
  predictPrice
};