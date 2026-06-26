"use client";
import { useDashboard, useAIFeed, useHotLeads, useAuth } from "@/hooks";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Users, Calendar, TrendingUp, DollarSign, Bot, Flame, AlertCircle, Clock } from "lucide-react";
import { cn, scoreColor, actionTypeLabel, timeAgo } from "@/lib/utils";
import Link from "next/link";

function MetricCard({ label, value, sub, icon: Icon, color }: any) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", color)}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-sm text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const { org } = useAuth();
  const { data: metrics, isLoading } = useDashboard();
  const { data: feed } = useAIFeed();
  const { data: hotLeads } = useHotLeads();

  if (isLoading) return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
      <div className="grid grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-32 animate-pulse bg-gray-100" />)}</div>
    </div>
  );

  const m = metrics!;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{org?.name}</h1>
        <p className="text-gray-500 text-sm mt-1">AI Sales Dashboard — your employee is working 24/7</p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Leads Received" value={m.leads_received} icon={Users} color="bg-blue-100 text-blue-600" sub="All inbound" />
        <MetricCard label="Meetings Booked" value={m.meetings_booked} icon={Calendar} color="bg-green-100 text-green-600" sub={`${m.conversion_rate}% conversion`} />
        <MetricCard label="Pipeline Value" value={`$${Math.round(m.pipeline_value).toLocaleString()}`} icon={DollarSign} color="bg-purple-100 text-purple-600" sub="Estimated total" />
        <MetricCard label="AI Actions Taken" value={m.ai_actions_taken} icon={Bot} color="bg-orange-100 text-orange-600" sub={`${m.followups_sent} follow-ups sent`} />
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{m.leads_contacted}</p>
          <p className="text-xs text-gray-500 mt-1">Leads Contacted</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{m.hot_leads}</p>
          <p className="text-xs text-gray-500 mt-1">🔥 Hot Leads</p>
        </div>
        <div className={cn("card p-4 text-center", m.leads_needing_human > 0 ? "border-orange-300 bg-orange-50" : "")}>
          <p className={cn("text-2xl font-bold", m.leads_needing_human > 0 ? "text-orange-600" : "text-gray-900")}>{m.leads_needing_human}</p>
          <p className="text-xs text-gray-500 mt-1">Need Human Attention</p>
          {m.leads_needing_human > 0 && <Link href="/leads?needs_human=true" className="text-xs text-orange-600 hover:underline">View →</Link>}
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{m.avg_response_time_minutes}m</p>
          <p className="text-xs text-gray-500 mt-1">Avg Response Time</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leads per day */}
        <div className="card p-6 lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Leads per Day</h3>
          {m.leads_by_day.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={m.leads_by_day} barSize={16}>
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9ca3af" }}
                  tickFormatter={(d) => new Date(d).toLocaleDateString("en", { month: "short", day: "numeric" })}
                  axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb", fontSize: 12 }} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-44 flex flex-col items-center justify-center text-gray-400 text-sm">
              <p className="font-medium">No leads yet</p>
              <p className="text-xs mt-1">Share your form link to start</p>
              <code className="mt-3 bg-gray-100 px-3 py-1 rounded text-xs text-gray-600">
                {typeof window !== "undefined" ? window.location.origin : ""}/form/{org?.slug}
              </code>
            </div>
          )}
        </div>

        {/* Score distribution */}
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Lead Quality</h3>
          <div className="space-y-3">
            {[
              { label: "🔥 High Intent", key: "high", color: "bg-red-500" },
              { label: "🌤 Medium Intent", key: "medium", color: "bg-amber-400" },
              { label: "❄️ Low Intent", key: "low", color: "bg-blue-400" },
            ].map(({ label, key, color }) => {
              const count = m.score_distribution[key as keyof typeof m.score_distribution] || 0;
              const pct = m.leads_received ? Math.round(count / m.leads_received * 100) : 0;
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{label}</span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hot leads */}
        {hotLeads && hotLeads.length > 0 && (
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <Flame className="w-4 h-4 text-red-500" /> Hot Leads to Watch
            </h3>
            <div className="space-y-3">
              {hotLeads.map((lead: any) => (
                <Link key={lead.id} href={`/leads/${lead.id}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{lead.full_name || lead.email}</p>
                    <p className="text-xs text-gray-500">{lead.company || "No company"}</p>
                  </div>
                  <div className="text-right">
                    <span className={cn("badge text-xs", scoreColor(lead.intent_score))}>{lead.intent_score}</span>
                    <p className="text-xs text-gray-400 mt-1">{lead.recommended_action?.slice(0, 30)}…</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* AI Actions Feed */}
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Bot className="w-4 h-4 text-primary-500" /> AI Activity Feed
          </h3>
          {feed && feed.length > 0 ? (
            <div className="space-y-3 max-h-72 overflow-y-auto">
              {feed.map((item: any) => (
                <div key={item.id} className="flex gap-3 text-sm">
                  <div className="w-2 h-2 rounded-full bg-primary-400 mt-1.5 shrink-0" />
                  <div>
                    <p className="text-gray-700">
                      <span className="font-medium">{actionTypeLabel(item.action_type)}</span>
                      {" for "}
                      <span className="text-primary-600">{item.lead_name}</span>
                    </p>
                    {item.reasoning && <p className="text-gray-400 text-xs mt-0.5 line-clamp-1">{item.reasoning}</p>}
                    <p className="text-gray-400 text-xs mt-0.5">{timeAgo(item.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No AI actions yet. Waiting for leads…</p>
          )}
        </div>
      </div>
    </div>
  );
}
