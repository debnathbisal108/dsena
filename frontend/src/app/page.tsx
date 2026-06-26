"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks";
export default function Home() {
  const { user, org, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading) {
      if (!user) router.replace("/login");
      else if (!org || !org.onboarding_complete) router.replace("/onboarding");
      else router.replace("/dashboard");
    }
  }, [user, org, loading, router]);
  return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>;
}
