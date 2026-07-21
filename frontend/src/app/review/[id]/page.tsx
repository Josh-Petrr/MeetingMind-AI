"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, 
  BrainCircuit, 
  CheckCircle2, 
  Clock, 
  User,
  ShieldCheck,
  Database,
  TrendingUp,
  AlertCircle
} from "lucide-react";

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = params.id as string;

  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Poll the backend until the meeting is processed
  useEffect(() => {
    let interval: NodeJS.Timeout;

    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/review/${meetingId}`);
        if (res.ok) {
          const json = await res.json();
          // If the pipeline status is complete or it has the data
          if (json.pipeline_status === "completed" || json.boris_output) {
            setData(json);
            setLoading(false);
            clearInterval(interval);
          }
        } else if (res.status === 404) {
          // Still processing, do nothing, let it poll
        } else {
          setError("Failed to fetch meeting data.");
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error(err);
        // keep polling
      }
    };

    fetchData(); // initial fetch
    interval = setInterval(fetchData, 3000); // poll every 3s

    return () => clearInterval(interval);
  }, [meetingId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <BrainCircuit className="w-16 h-16 text-blue-500 animate-pulse mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Analyzing Meeting</h2>
        <p className="text-slate-400 text-center max-w-md">
          Boris is summarizing the narrative. Anna is extracting tasks. Max is updating organizational memory...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-400">
        <AlertCircle className="w-12 h-12 mb-4" />
        <p>{error}</p>
        <button onClick={() => router.push("/")} className="mt-4 text-blue-400 underline">Go Back</button>
      </div>
    );
  }

  const { pii_report, boris_output, anna_output, max_output, timing } = data;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push("/")}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-3xl font-bold text-white tracking-tight">Intelligence Report</h2>
            <p className="text-slate-400">ID: <span className="font-mono text-xs text-slate-500">{meetingId}</span></p>
          </div>
        </div>
        
        <div className="flex gap-4">
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium">
            <ShieldCheck className="w-4 h-4" />
            {pii_report?.pii_count || 0} PII Items Masked
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium">
            <Database className="w-4 h-4" />
            {max_output?.stored_count || 0} Memories Saved
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Executive Summary (Boris) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex items-center gap-2 mb-4">
              <BrainCircuit className="w-5 h-5 text-purple-400" />
              <h3 className="text-xl font-semibold text-white">Executive Summary</h3>
            </div>
            <div className="prose prose-invert max-w-none">
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {boris_output?.summary || "No summary available."}
              </p>
            </div>
            
            {/* Key Topics Badges */}
            {boris_output?.key_topics && boris_output.key_topics.length > 0 && (
              <div className="mt-6 flex flex-wrap gap-2">
                {boris_output.key_topics.map((topic: string, i: number) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-slate-300">
                    {topic}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Decisions */}
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Key Decisions
            </h3>
            
            <div className="space-y-3">
              {(anna_output?.decisions || []).length > 0 ? (
                anna_output.decisions.map((dec: any, i: number) => (
                  <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5 flex gap-4">
                    <div className="flex-1">
                      <p className="text-slate-200 font-medium mb-1">{dec.decision}</p>
                      {dec.made_by && (
                        <p className="text-xs text-slate-400 flex items-center gap-1">
                          <User className="w-3 h-3" /> Proposed by {dec.made_by}
                        </p>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-400 italic">No explicit decisions extracted.</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar (Action Items) */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl h-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-amber-400" />
                Action Items
              </h3>
              <span className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold text-slate-300">
                {anna_output?.total_action_items || 0}
              </span>
            </div>

            <div className="space-y-4">
              {(anna_output?.action_items || []).length > 0 ? (
                anna_output.action_items.map((item: any, i: number) => (
                  <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5 relative overflow-hidden group hover:border-amber-500/30 transition-colors">
                    <div className={`absolute top-0 left-0 w-1 h-full ${
                      item.priority === 'high' ? 'bg-red-500' : 
                      item.priority === 'medium' ? 'bg-amber-500' : 'bg-blue-500'
                    }`} />
                    <p className="text-sm text-slate-200 font-medium mb-3 pl-2">{item.task}</p>
                    <div className="flex items-center justify-between pl-2">
                      <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        <User className="w-3 h-3" />
                        {item.owner}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-amber-400/80">
                        <Clock className="w-3 h-3" />
                        {item.deadline}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-400 italic text-sm">No action items extracted.</p>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
