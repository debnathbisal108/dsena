export interface User { id:string; email:string; full_name:string; is_verified:boolean; avatar_url?:string; created_at:string; }
export interface Organization {
  id:string; name:string; slug:string; description?:string; services?:string;
  target_customer?:string; pricing_guidance?:string; faqs?:string; business_rules?:string;
  website_url?:string; ai_tone:string; max_followup_attempts:number;
  allowed_hours_start:number; allowed_hours_end:number; allowed_timezone:string;
  onboarding_complete:boolean; onboarding_step:number; created_at:string;
}
export interface Lead {
  id:string; email:string; full_name?:string; phone?:string; company?:string;
  role?:string; message?:string; status:string;
  intent_score:number; urgency_score:number; buying_probability:number;
  estimated_deal_value?:number; sentiment?:string;
  detected_objections?:string[]; qualification_summary?:string;
  recommended_action?:string; risk_factors?:string[];
  spam_risk_score:number; followup_count:number; human_takeover:boolean;
  stop_reason?:string; last_ai_action?:string; next_action_at?:string;
  utm_source?:string; conversation?:Conversation;
  ai_actions?:AIAction[]; meetings?:Meeting[];
  created_at:string; updated_at:string;
}
export interface Message { id:string; role:string; content:string; sent_via?:string; opened_at?:string; created_at:string; }
export interface Conversation { id:string; messages:Message[]; created_at:string; }
export interface AIAction {
  id:string; action_type:string; reasoning?:string;
  response_content?:string; tokens_used?:number; model_used?:string; created_at:string;
}
export interface Meeting { id:string; meet_link?:string; starts_at:string; ends_at:string; status:string; created_at:string; }
export interface PaginatedLeads { items:Lead[]; total:number; page:number; pages:number; }
export interface DashboardMetrics {
  leads_received:number; leads_contacted:number; meetings_booked:number;
  pipeline_value:number; conversion_rate:number; ai_actions_taken:number;
  followups_sent:number; hot_leads:number; leads_needing_human:number;
  avg_response_time_minutes:number; leads_by_day:{date:string;count:number}[];
  score_distribution:{high:number;medium:number;low:number};
}
export interface KnowledgeChunk { id:string; source_type:string; source_url?:string; title?:string; content:string; created_at:string; }
export interface CrawlJob { id:string; url:string; status:string; pages_found:number; chunks_created:number; error?:string; created_at:string; completed_at?:string; }
export interface AIFeedItem { id:string; lead_name:string; action_type:string; reasoning?:string; created_at:string; }
