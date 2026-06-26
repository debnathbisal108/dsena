"use client";
import { useState } from "react";
import Link from "next/link";
import { useLeads } from "@/hooks";
import { cn, scoreColor, scoreLabel, statusColor, timeAgo } from "@/lib/utils";
import { Search, ChevronLeft, ChevronRight, AlertCircle, Bot } from "lucide-react";

export default function LeadsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [needsHuman, setNeedsHuman] = useState(false);

  const { data, isLoading } = useLeads({ page, search, status, needs_human: needsHuman });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        <span className="text-sm text-gray-500">{data?.total ?? 0} total</span>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input className="input pl-9" placeholder="Search name, email, company…" value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <select className="input w-auto" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          {["new","ai_contacted","nurturing","meeting_proposed","meeting_booked","qualified","disqualified","stopped","needs_human"].map(s => (
            <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
          ))}
        </select>
        <label className={cn("flex items-center gap-2 px-3 py-2 rounded-lg border text-sm cursor-pointer transition-colors",
          needsHuman ? "bg-orange-50 border-orange-300 text-orange-700" : "border-gray-300 text-gray-600 hover:bg-gray-50")}>
          <input type="checkbox" checked={needsHuman} onChange={(e) => { setNeedsHuman(e.target.checked); setPage(1); }} className="sr-only" />
          <AlertCircle className="w-4 h-4" /> Needs Human
        </label>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-500">Lead</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Company</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Intent</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">AI Actions</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">When</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading
              ? [...Array(8)].map((_, i) => (
                <tr key={i}>{[...Array(6)].map((_, j) => (
                  <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-100 rounded animate-pulse" /></td>
                ))}</tr>
              ))
              : data?.items.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <Link href={`/leads/${lead.id}`} className="block">
                      <p className="font-medium text-gray-900 hover:text-primary-600 transition-colors flex items-center gap-2">
                        {lead.full_name || lead.email}
                        {lead.human_takeover && <AlertCircle className="w-3 h-3 text-orange-500" />}
                      </p>
                      <p className="text-gray-400 text-xs">{lead.email}</p>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{lead.company || "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      <span className={cn("badge text-xs", scoreColor(lead.intent_score))}>
                        {scoreLabel(lead.intent_score)}
                      </span>
                      <div className="flex gap-1">
                        <div className="h-1 rounded-full bg-gray-100 flex-1 overflow-hidden">
                          <div className="h-full bg-primary-500 rounded-full" style={{ width: `${lead.intent_score}%` }} />
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("badge", statusColor(lead.status))}>
                      {lead.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-gray-500">
                      <Bot className="w-3 h-3" />
                      <span className="text-xs">{lead.followup_count} sent</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{timeAgo(lead.created_at)}</td>
                </tr>
              ))}
          </tbody>
        </table>

        {data?.items.length === 0 && !isLoading && (
          <div className="text-center py-16 text-gray-400">
            <p className="font-medium">No leads yet</p>
            <p className="text-sm mt-1">Share your form link to start capturing leads.</p>
          </div>
        )}
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Page {data.page} of {data.pages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary px-3 py-1 disabled:opacity-40">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} className="btn-secondary px-3 py-1 disabled:opacity-40">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
