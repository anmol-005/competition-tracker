import { useQuery } from '@tanstack/react-query';
import type { Product } from '@shared/schema';

interface ProductsResponse {
  success: boolean;
  count: number;
  products: Product[];
  error?: string; // Optional error message
  message?: string; // Optional message
}

interface ProductResponse {
  success: boolean;
  product: Product;
  error?: string; // Optional error message
}

// Hook to fetch all products from database
export function useProducts() {
  return useQuery({
    queryKey: ['products'],
    queryFn: async (): Promise<Product[]> => {
      try {
        const response = await fetch('/api/products');
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to fetch products`);
        }
        
        const data: ProductsResponse = await response.json();
        
        if (!data.success) {
          throw new Error(data.error || data.message || 'Failed to fetch products from database');
        }
        
        // Ensure we return an array
        return Array.isArray(data.products) ? data.products : [];
        
      } catch (error) {
        console.error('Error fetching products:', error);
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 2, // Retry failed requests 2 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  });
}

// Hook to fetch single product by ASIN
export function useProduct(asin: string) {
  return useQuery({
    queryKey: ['product', asin],
    queryFn: async (): Promise<Product> => {
      try {
        const response = await fetch(`/api/products/${asin}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Product with ASIN ${asin} not found`);
          }
          throw new Error(`HTTP ${response.status}: Failed to fetch product`);
        }
        
        const data: ProductResponse = await response.json();
        
        if (!data.success) {
          throw new Error(data.error || `Product ${asin} not found`);
        }
        
        return data.product;
        
      } catch (error) {
        console.error(`Error fetching product ${asin}:`, error);
        throw error;
      }
    },
    enabled: !!asin, // Only run if ASIN is provided
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 1, // Only retry once for individual products
  });
}

// Hook to check API health
export function useApiHealth() {
  return useQuery({
    queryKey: ['api-health'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/health');
        
        if (!response.ok) {
          throw new Error(`API health check failed: HTTP ${response.status}`);
        }
        
        return response.json();
        
      } catch (error) {
        console.error('API health check error:', error);
        throw error;
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 60 * 1000, // 1 minute
    retry: 1, // Only retry once for health checks
  });
}