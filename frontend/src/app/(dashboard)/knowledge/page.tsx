"use client";
import { useState } from "react";
import { useKnowledgeStats } from "@/hooks";
import api from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Brain, Globe, FileText, Plus, Trash2, RefreshCw, CheckCircle, Loader2 } from "lucide-react";
import { getErrorMessage, timeAgo, cn } from "@/lib/utils";

export default function KnowledgePage() {
  const { data: stats } = useKnowledgeStats();
  const qc = useQueryClient();
  const [crawlUrl, setCrawlUrl] = useState("");
  const [crawling, setCrawling] = useState(false);
  const [manualTitle, setManualTitle] = useState("");
  const [manualContent, setManualContent] = useState("");
  const [error, setError] = useState("");

  const { data: chunks } = useQuery({
    queryKey: ["knowledge-chunks"],
    queryFn: async () => (await api.get("/api/knowledge/chunks")).data,
  });

  const { data: docs } = useQuery({
    queryKey: ["knowledge-docs"],
    queryFn: async () => (await api.get("/api/knowledge/documents")).data,
  });

  const { data: jobs } = useQuery({
    queryKey: ["crawl-jobs"],
    queryFn: async () => (await api.get("/api/knowledge/crawl-jobs")).data,
    refetchInterval: 5000,
  });

  async function startCrawl() {
    if (!crawlUrl) return;
    setCrawling(true); setError("");
    try {
      await api.post("/api/onboarding/crawl-website", { url: crawlUrl });
      setCrawlUrl("");
      qc.invalidateQueries({ queryKey: ["crawl-jobs"] });
      qc.invalidateQueries({ queryKey: ["knowledge-stats"] });
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setCrawling(false); }
  }

  async function deleteChunk(id: string) {
    try {
      await api.delete(`/api/knowledge/chunks/${id}`);
      qc.invalidateQueries({ queryKey: ["knowledge-chunks"] });
      qc.invalidateQueries({ queryKey: ["knowledge-stats"] });
    } catch (e) { setError(getErrorMessage(e)); }
  }

  async function addManual() {
    if (!manualTitle || !manualContent) return;
    setError("");
    try {
      await api.post("/api/onboarding/add-manual-knowledge", { title: manualTitle, content: manualContent });
      setManualTitle(""); setManualContent("");
      qc.invalidateQueries({ queryKey: ["knowledge-chunks"] });
      qc.invalidateQueries({ queryKey: ["knowledge-stats"] });
    } catch (e) { setError(getErrorMessage(e)); }
  }

  async function uploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    try {
      await api.post("/api/onboarding/upload-document", form, { headers: { "Content-Type": "multipart/form-data" } });
      qc.invalidateQueries({ queryKey: ["knowledge-docs"] });
      qc.invalidateQueries({ queryKey: ["knowledge-stats"] });
    } catch (e) { setError(getErrorMessage(e)); }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Knowledge Base</h1>
        <p className="text-gray-500 text-sm mt-1">Everything your AI knows about your business</p>
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{stats.total_chunks}</p>
            <p className="text-xs text-gray-500 mt-1">Knowledge Chunks</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{stats.total_documents}</p>
            <p className="text-xs text-gray-500 mt-1">Documents</p>
          </div>
          <div className="card p-4 text-center">
            <p className={cn("text-2xl font-bold", stats.last_crawl_status === "done" ? "text-green-600" : "text-gray-900")}>
              {stats.last_crawl_status || "—"}
            </p>
            <p className="text-xs text-gray-500 mt-1">Last Crawl Status</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Crawl website */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
            <Globe className="w-4 h-4 text-primary-500" /> Crawl a Website
          </h3>
          <p className="text-sm text-gray-500 mb-4">AI reads every page and builds knowledge automatically.</p>
          <div className="flex gap-2">
            <input className="input flex-1" placeholder="https://yoursite.com" value={crawlUrl}
              onChange={(e) => setCrawlUrl(e.target.value)} />
            <button onClick={startCrawl} disabled={crawling || !crawlUrl} className="btn-primary flex items-center gap-2 shrink-0">
              {crawling ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              {crawling ? "Crawling…" : "Crawl"}
            </button>
          </div>

          {/* Crawl jobs */}
          {jobs && jobs.length > 0 && (
            <div className="mt-4 space-y-2">
              {jobs.slice(0, 3).map((job: any) => (
                <div key={job.id} className="flex items-center justify-between text-sm bg-gray-50 rounded-lg p-2">
                  <span className="text-gray-600 truncate max-w-48">{job.url}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-gray-400">{job.pages_found}p · {job.chunks_created}c</span>
                    <span className={cn("badge text-xs",
                      job.status === "done" ? "bg-green-100 text-green-700" :
                      job.status === "running" ? "bg-blue-100 text-blue-700" :
                      job.status === "failed" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600")}>
                      {job.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upload document */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary-500" /> Upload Documents
          </h3>
          <p className="text-sm text-gray-500 mb-4">PDFs, pricing sheets, service docs, case studies.</p>
          <label className="btn-secondary w-full text-center cursor-pointer flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" /> Choose PDF or Text File
            <input type="file" accept=".pdf,.txt,.md" className="sr-only" onChange={uploadFile} />
          </label>

          {docs && docs.length > 0 && (
            <div className="mt-4 space-y-2">
              {docs.map((doc: any) => (
                <div key={doc.id} className="flex items-center justify-between text-sm bg-gray-50 rounded-lg p-2">
                  <span className="text-gray-700 truncate max-w-48">{doc.filename}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-gray-400">{doc.chunks_created} chunks</span>
                    <span className={cn("badge text-xs",
                      doc.status === "done" ? "bg-green-100 text-green-700" :
                      doc.status === "processing" ? "bg-blue-100 text-blue-700" :
                      "bg-red-100 text-red-700")}>
                      {doc.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add manual knowledge */}
      <div className="card p-6">
        <h3 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <Brain className="w-4 h-4 text-primary-500" /> Add Manual Knowledge
        </h3>
        <p className="text-sm text-gray-500 mb-4">Add FAQs, pricing details, case studies, or anything else you want AI to know.</p>
        <div className="space-y-3">
          <input className="input" placeholder="Title (e.g. 'Pricing FAQ')" value={manualTitle} onChange={(e) => setManualTitle(e.target.value)} />
          <textarea className="input h-32 resize-none" placeholder="Content…" value={manualContent} onChange={(e) => setManualContent(e.target.value)} />
          <button onClick={addManual} disabled={!manualTitle || !manualContent} className="btn-primary">Add to Knowledge Base</button>
        </div>
      </div>

      {/* Knowledge chunks list */}
      {chunks && chunks.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-700">Knowledge Chunks ({chunks.length})</h3>
          </div>
          <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
            {chunks.map((chunk: any) => (
              <div key={chunk.id} className="px-6 py-4 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn("badge text-xs",
                      chunk.source_type === "website" ? "bg-blue-100 text-blue-700" :
                      chunk.source_type === "pdf" ? "bg-purple-100 text-purple-700" :
                      "bg-green-100 text-green-700")}>
                      {chunk.source_type}
                    </span>
                    {chunk.title && <span className="text-sm font-medium text-gray-700 truncate">{chunk.title}</span>}
                  </div>
                  <p className="text-sm text-gray-500 line-clamp-2">{chunk.content}</p>
                </div>
                <button onClick={() => deleteChunk(chunk.id)} className="text-gray-400 hover:text-red-500 transition-colors shrink-0 p-1">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
