"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, Brain, Settings, LogOut, Zap, AlertCircle } from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/knowledge", label: "Knowledge Base", icon: Brain },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, org, logout } = useAuth();

  return (
    <aside className="w-60 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 leading-none">AI Sales</p>
            <p className="text-xs text-gray-500 mt-0.5">Employee</p>
          </div>
        </div>
      </div>

      {org && (
        <div className="px-4 py-3 border-b border-gray-100">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">Organization</p>
          <p className="text-sm font-medium text-gray-800 truncate">{org.name}</p>
          <p className="text-xs text-gray-400 mt-0.5">Tone: {org.ai_tone}</p>
        </div>
      )}

      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href} className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              active ? "bg-primary-50 text-primary-700" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            )}>
              <Icon className="w-4 h-4" />{label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 font-semibold text-sm">
            {user?.full_name?.[0]?.toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button onClick={logout} className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition-colors w-full">
          <LogOut className="w-4 h-4" /> Sign out
        </button>
      </div>
    </aside>
  );
}
