"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks";
export default function AuthCallback() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  useEffect(() => {
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");
    if (access && refresh) login(access, refresh).then(() => router.replace("/"));
    else router.replace("/login?error=oauth_failed");
  }, []);
  return <div className="min-h-screen flex items-center justify-center"><div className="text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4" /><p className="text-gray-500">Signing you in…</p></div></div>;
}
