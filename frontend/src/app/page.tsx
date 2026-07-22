"use client";

import { useState, useEffect } from "react";
import { UploadCloud, Bot, ArrowRight, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [transcript, setTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const router = useRouter();

  // Load from session storage to persist across tabs
  useEffect(() => {
    const saved = sessionStorage.getItem("draftTranscript");
    if (saved) setTranscript(saved);
  }, []);

  // Save to session storage whenever it changes
  useEffect(() => {
    sessionStorage.setItem("draftTranscript", transcript);
  }, [transcript]);

  const handleProcess = async () => {
    if (!transcript.trim()) return;

    setIsProcessing(true);
    try {
      const response = await fetch("http://localhost:8000/process-meeting", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transcript: transcript,
          org_id: "org_demo_123",
          // Let the backend generate the meeting_id if not provided
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to process meeting");
      }

      const data = await response.json();
      
      // Add to global poller list so we can notify the user from anywhere
      const pendingStr = sessionStorage.getItem("pendingMeetings");
      const pendingList = pendingStr ? JSON.parse(pendingStr) : [];
      pendingList.push(data.meeting_id);
      sessionStorage.setItem("pendingMeetings", JSON.stringify(pendingList));

      // Show a toast that background processing started
      const { toast } = await import("react-hot-toast");
      toast("Agents dispatched! We'll notify you when extraction is complete.", {
        icon: '🚀',
        style: { background: '#1e293b', color: '#fff' }
      });

      // Navigate to the review page right away. 
      router.push(`/review/${data.meeting_id}`);
    } catch (error) {
      console.error(error);
      alert("An error occurred while processing the meeting.");
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto h-full flex flex-col">
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Process New Meeting</h2>
        <p className="text-slate-400">
          Paste your raw meeting transcript below. Our agentic squad will mask PII, summarize the narrative, and extract decisions.
        </p>
      </header>

      <div className="flex-1 glass-panel rounded-2xl p-6 flex flex-col gap-6 relative">
        {isProcessing && (
          <div className="absolute inset-0 z-10 bg-slate-900/50 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Awakening Agents...</h3>
            <p className="text-slate-300">Boris, Anna, and Max are reviewing the transcript.</p>
          </div>
        )}

        <div className="flex-1 flex flex-col">
          <label className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
            <FileTextIcon className="w-4 h-4" />
            Raw Transcript
          </label>
          <textarea
            className="flex-1 w-full bg-slate-900/50 border border-white/10 rounded-xl p-4 text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none font-mono text-sm leading-relaxed"
            placeholder="[10:00 AM] Sarah: Let's discuss the roadmap...&#10;[10:01 AM] John: Sure, my SSN is..."
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
          />
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-white/10">
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <Bot className="w-5 h-5 text-purple-400" />
            Protected by Presidio PII Masking
          </div>
          <button
            onClick={handleProcess}
            disabled={!transcript.trim() || isProcessing}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20"
          >
            {isProcessing ? "Processing..." : "Extract Intelligence"}
            {!isProcessing && <ArrowRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

function FileTextIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 0 0 2 2h12a2 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" x2="8" y1="13" y2="13" />
      <line x1="16" x2="8" y1="17" y2="17" />
      <line x1="10" x2="8" y1="9" y2="9" />
    </svg>
  );
}
