"use client";
import { useParams, useRouter } from "next/navigation";
import { useLead, useLeadActions } from "@/hooks";
import { cn, scoreColor, scoreLabel, statusColor, formatDateTime, timeAgo, actionTypeLabel } from "@/lib/utils";
import { ArrowLeft, Phone, Building, Bot, AlertCircle, CheckCircle, UserX, Zap, Calendar } from "lucide-react";
import Link from "next/link";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-500">{label}</span>
        <span className={cn("font-bold", color)}>{value}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color.includes("red") ? "bg-red-500" : color.includes("amber") ? "bg-amber-400" : color.includes("green") ? "bg-green-500" : "bg-primary-500")}
          style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: lead, isLoading, refetch } = useLead(id);
  const actions = useLeadActions(id);

  if (isLoading) return (
    <div className="space-y-6">
      <div className="h-8 w-32 bg-gray-200 rounded animate-pulse" />
      <div className="grid grid-cols-3 gap-6">{[...Array(3)].map((_, i) => <div key={i} className="card p-6 h-64 animate-pulse bg-gray-100" />)}</div>
    </div>
  );
  if (!lead) return <div className="text-gray-500">Lead not found.</div>;

  const intentColor = lead.intent_score >= 70 ? "text-red-600" : lead.intent_score >= 40 ? "text-amber-600" : "text-blue-600";

  return (
    <div className="space-y-6">
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to leads
      </button>

      {lead.human_takeover && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-orange-700 text-sm">
            <AlertCircle className="w-4 h-4" />
            <strong>Human attention needed</strong> — AI has paused outreach for this lead
          </div>
          <button onClick={() => actions.releaseToAI.mutate()} className="text-xs btn-secondary px-3 py-1">
            Release back to AI
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Lead info + AI Intelligence */}
        <div className="space-y-4">
          {/* Basic info */}
          <div className="card p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900">{lead.full_name || lead.email}</h2>
                <p className="text-gray-500 text-sm">{lead.email}</p>
              </div>
              <span className={cn("badge", statusColor(lead.status))}>{lead.status.replace(/_/g, " ")}</span>
            </div>
            <div className="space-y-2 text-sm">
              {lead.phone && <div className="flex items-center gap-2 text-gray-600"><Phone className="w-3.5 h-3.5 text-gray-400" />{lead.phone}</div>}
              {lead.company && <div className="flex items-center gap-2 text-gray-600"><Building className="w-3.5 h-3.5 text-gray-400" />{lead.company}</div>}
              {lead.role && <p className="text-gray-500">{lead.role}</p>}
            </div>
            <p className="text-xs text-gray-400 mt-3">Submitted {timeAgo(lead.created_at)}</p>

            {/* Action buttons */}
            <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
              {!lead.human_takeover && (
                <button onClick={() => actions.humanTakeover.mutate()} className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1">
                  <UserX className="w-3 h-3" /> Take over
                </button>
              )}
              <button onClick={() => actions.forceFollowup.mutate()} className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1">
                <Zap className="w-3 h-3" /> Force AI action
              </button>
              <button onClick={() => actions.disqualify.mutate()} className="text-xs px-3 py-1.5 text-red-500 hover:text-red-700 border border-red-200 rounded-lg flex items-center gap-1">
                <UserX className="w-3 h-3" /> Disqualify
              </button>
            </div>
          </div>

          {/* AI Intelligence Panel */}
          <div className="card p-6">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4 flex items-center gap-1">
              <Bot className="w-3.5 h-3.5" /> AI Intelligence
            </h3>
            <div className="space-y-3 mb-4">
              <ScoreBar label="Intent Score" value={lead.intent_score} color={intentColor} />
              <ScoreBar label="Urgency" value={lead.urgency_score} color="text-amber-600" />
              <ScoreBar label="Buying Probability" value={lead.buying_probability} color="text-green-600" />
            </div>
            <div className="space-y-2 text-sm">
              {lead.sentiment && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Sentiment</span>
                  <span className={cn("font-medium capitalize",
                    lead.sentiment === "positive" ? "text-green-600" :
                    lead.sentiment === "negative" ? "text-red-600" : "text-gray-600")}>
                    {lead.sentiment}
                  </span>
                </div>
              )}
              {lead.estimated_deal_value && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Est. Deal Value</span>
                  <span className="font-medium text-gray-900">${lead.estimated_deal_value.toLocaleString()}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">Follow-ups Sent</span>
                <span className="font-medium text-gray-900">{lead.followup_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Spam Risk</span>
                <span className={cn("font-medium", lead.spam_risk_score >= 60 ? "text-red-600" : "text-green-600")}>
                  {lead.spam_risk_score}/100
                </span>
              </div>
            </div>
          </div>

          {/* Qualification Summary */}
          {lead.qualification_summary && (
            <div className="card p-5">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">AI Summary</h3>
              <p className="text-sm text-gray-700 leading-relaxed">{lead.qualification_summary}</p>
              {lead.recommended_action && (
                <div className="mt-3 p-2 bg-primary-50 rounded-lg">
                  <p className="text-xs font-medium text-primary-700">Recommended: {lead.recommended_action}</p>
                </div>
              )}
            </div>
          )}

          {/* Objections */}
          {lead.detected_objections && lead.detected_objections.length > 0 && (
            <div className="card p-5">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Detected Objections</h3>
              <ul className="space-y-1">
                {lead.detected_objections.map((obj, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-amber-500 mt-0.5">•</span>{obj}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Stop reason */}
          {lead.stop_reason && (
            <div className="card p-4 border-gray-200 bg-gray-50">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Outreach Stopped</p>
              <p className="text-sm text-gray-600">{lead.stop_reason}</p>
            </div>
          )}

          {/* Meetings */}
          {lead.meetings && lead.meetings.length > 0 && (
            <div className="card p-5">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" /> Meetings
              </h3>
              {lead.meetings.map((m) => (
                <div key={m.id} className="text-sm">
                  <p className="font-medium text-gray-900">{formatDateTime(m.starts_at)}</p>
                  <p className={cn("text-xs mt-0.5", m.status === "confirmed" ? "text-green-600" : "text-red-500")}>{m.status}</p>
                  {m.meet_link && (
                    <a href={m.meet_link} target="_blank" rel="noopener noreferrer" className="text-primary-600 text-xs hover:underline">
                      Join Google Meet →
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Middle + Right: Conversation */}
        <div className="lg:col-span-2 space-y-4">
          {/* Conversation thread */}
          <div className="card flex flex-col" style={{ maxHeight: "55vh" }}>
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">Email Conversation</h3>
              <span className="text-xs text-gray-400">{lead.conversation?.messages?.length ?? 0} messages</span>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {!lead.conversation || lead.conversation.messages.length === 0 ? (
                <div className="text-center py-12 text-gray-400 text-sm">AI qualification in progress…</div>
              ) : (
                lead.conversation.messages.map((msg) => (
                  <div key={msg.id} className={cn("flex", msg.role === "ai" ? "justify-start" : "justify-end")}>
                    <div className={cn("max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                      msg.role === "ai" ? "bg-gray-100 text-gray-800 rounded-tl-sm" :
                      msg.role === "lead" ? "bg-primary-600 text-white rounded-tr-sm" :
                      "bg-green-100 text-green-800 rounded-tr-sm")}>
                      {msg.role === "ai" && <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Bot className="w-3 h-3" /> AI</p>}
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <p className={cn("text-xs mt-1.5", msg.role === "ai" ? "text-gray-400" : "text-primary-200")}>
                        {timeAgo(msg.created_at)}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* AI Reasoning Log */}
          {lead.ai_actions && lead.ai_actions.length > 0 && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <Bot className="w-4 h-4 text-primary-500" /> AI Reasoning Log
              </h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {lead.ai_actions.map((action) => (
                  <div key={action.id} className="flex gap-3 text-sm border-l-2 border-primary-100 pl-3">
                    <div>
                      <p className="font-medium text-gray-800">{actionTypeLabel(action.action_type)}</p>
                      {action.reasoning && <p className="text-gray-500 text-xs mt-0.5">{action.reasoning}</p>}
                      <p className="text-gray-400 text-xs mt-1">{timeAgo(action.created_at)} · {action.tokens_used} tokens</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
