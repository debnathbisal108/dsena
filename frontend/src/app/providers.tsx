"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, ReactNode } from "react";
import { AuthProvider } from "@/hooks";

export function Providers({ children }: { children: ReactNode }) {
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 30000, retry: 1 } } }));
  return <QueryClientProvider client={qc}><AuthProvider>{children}</AuthProvider></QueryClientProvider>;
}
