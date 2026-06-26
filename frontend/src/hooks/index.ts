"use client";
import { createContext, useContext, useReducer, useEffect, ReactNode } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { User, Organization, PaginatedLeads, Lead, DashboardMetrics, AIFeedItem } from "@/types";
import api from "@/lib/api";

// ── Auth Context ──────────────────────────────────────────────────────────
interface AuthState { user: User | null; org: Organization | null; loading: boolean; }
type AuthAction = { type: "SET"; user: User; org: Organization | null } | { type: "SET_ORG"; org: Organization } | { type: "LOGOUT" } | { type: "LOADING"; v: boolean };

function reducer(s: AuthState, a: AuthAction): AuthState {
  if (a.type === "SET") return { ...s, user: a.user, org: a.org, loading: false };
  if (a.type === "SET_ORG") return { ...s, org: a.org };
  if (a.type === "LOGOUT") return { user: null, org: null, loading: false };
  if (a.type === "LOADING") return { ...s, loading: a.v };
  return s;
}

interface AuthCtx extends AuthState { login: (a: string, r: string) => Promise<void>; logout: () => void; setOrg: (o: Organization) => void; }
const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, { user: null, org: null, loading: true });

  useEffect(() => {
    if (localStorage.getItem("access_token")) fetchUser();
    else dispatch({ type: "LOADING", v: false });
  }, []);

  async function fetchUser() {
    try {
      const [u, o] = await Promise.all([api.get("/api/auth/me"), api.get("/api/onboarding/status").catch(() => ({ data: null }))]);
      dispatch({ type: "SET", user: u.data, org: o.data });
    } catch { dispatch({ type: "LOGOUT" }); }
  }

  async function login(access: string, refresh: string) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    await fetchUser();
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    dispatch({ type: "LOGOUT" });
    window.location.href = "/login";
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setOrg: (o) => dispatch({ type: "SET_ORG", org: o }) }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const c = useContext(AuthContext);
  if (!c) throw new Error("useAuth must be inside AuthProvider");
  return c;
}

// ── Data Hooks ────────────────────────────────────────────────────────────
export function useLeads(filters: { page?: number; status?: string; search?: string; needs_human?: boolean } = {}) {
  return useQuery<PaginatedLeads>({
    queryKey: ["leads", filters],
    queryFn: async () => {
      const p = new URLSearchParams();
      if (filters.page) p.set("page", String(filters.page));
      if (filters.status) p.set("status", filters.status);
      if (filters.search) p.set("search", filters.search);
      if (filters.needs_human) p.set("needs_human", "true");
      return (await api.get(`/api/leads?${p}`)).data;
    },
  });
}

export function useLead(id: string) {
  return useQuery<Lead>({
    queryKey: ["lead", id],
    queryFn: async () => (await api.get(`/api/leads/${id}`)).data,
    enabled: !!id,
  });
}

export function useLeadActions(id: string) {
  const qc = useQueryClient();
  const invalidate = () => { qc.invalidateQueries({ queryKey: ["lead", id] }); qc.invalidateQueries({ queryKey: ["leads"] }); };
  const humanTakeover = useMutation({ mutationFn: () => api.post(`/api/leads/${id}/human-takeover`), onSuccess: invalidate });
  const releaseToAI = useMutation({ mutationFn: () => api.post(`/api/leads/${id}/release-to-ai`), onSuccess: invalidate });
  const disqualify = useMutation({ mutationFn: () => api.post(`/api/leads/${id}/disqualify`), onSuccess: invalidate });
  const forceFollowup = useMutation({ mutationFn: () => api.post(`/api/leads/${id}/force-followup`), onSuccess: invalidate });
  return { humanTakeover, releaseToAI, disqualify, forceFollowup };
}

export function useDashboard(from?: string, to?: string) {
  return useQuery<DashboardMetrics>({
    queryKey: ["dashboard", from, to],
    queryFn: async () => {
      const p = new URLSearchParams();
      if (from) p.set("from_date", from);
      if (to) p.set("to_date", to);
      return (await api.get(`/api/dashboard/metrics?${p}`)).data;
    },
  });
}

export function useAIFeed() {
  return useQuery<AIFeedItem[]>({
    queryKey: ["ai-feed"],
    queryFn: async () => (await api.get("/api/dashboard/ai-feed")).data,
    refetchInterval: 30000,
  });
}

export function useHotLeads() {
  return useQuery({ queryKey: ["hot-leads"], queryFn: async () => (await api.get("/api/dashboard/hot-leads")).data, refetchInterval: 60000 });
}

export function useKnowledgeStats() {
  return useQuery({ queryKey: ["knowledge-stats"], queryFn: async () => (await api.get("/api/knowledge/stats")).data });
}

export function useCalendarStatus() {
  return useQuery({ queryKey: ["calendar-status"], queryFn: async () => (await api.get("/api/calendar/status")).data });
}
