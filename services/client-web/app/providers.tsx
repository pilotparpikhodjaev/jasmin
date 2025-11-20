"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { useAuthStore } from "@/lib/stores/auth-store";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  // Ensure auth loading flag settles after hydration so guarded routes can render
  const setLoading = useAuthStore((state) => state.setLoading);
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const storedUser = useAuthStore((state) => state.user);
  const storedToken = useAuthStore((state) => state.token);
  const storedRefresh = useAuthStore((state) => state.refreshToken);

  useEffect(() => {
    if (storedUser && storedToken && storedRefresh) {
      setAuth(storedUser, storedToken, storedRefresh);
    } else {
      clearAuth();
    }
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
}
