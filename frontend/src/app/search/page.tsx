"use client";

import { useState, useRef, useEffect } from "react";
import { Send, BrainCircuit, Loader2, ArrowRight, Bot, User } from "lucide-react";
import Link from "next/link";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
}

export default function SearchPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I have access to all your past meeting memories. What would you like to know?"
    }
  ]);
  const [query, setQuery] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages from sessionStorage
  useEffect(() => {
    const saved = sessionStorage.getItem("chatMessages");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {}
    }
  }, []);

  // Save messages to sessionStorage whenever they change
  useEffect(() => {
    sessionStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg = query.trim();
    setQuery("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsTyping(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg, org_id: "org_demo_123" }),
      });

      if (!res.ok) throw new Error("Chat failed");

      const data = await res.json();
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources }
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error searching the memory banks." }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto p-4 md:p-8">
      <header className="mb-6 flex items-center gap-3">
        <BrainCircuit className="w-8 h-8 text-blue-500" />
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Interactive RAG</h2>
          <p className="text-slate-400 text-sm">Chat with your organizational memory</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto space-y-6 mb-6 pr-2 scrollbar-thin scrollbar-thumb-white/10">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0 border border-blue-500/30 mt-2">
                <Bot className="w-5 h-5 text-blue-400" />
              </div>
            )}
            
            <div className={`max-w-[85%] rounded-2xl p-5 shadow-lg ${
              msg.role === "user" 
                ? "bg-blue-600 text-white rounded-br-none" 
                : "glass-panel rounded-bl-none border border-white/10"
            }`}>
              <div className="prose prose-invert max-w-none">
                <p className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>
              </div>
              
              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-5 pt-4 border-t border-white/10 space-y-3">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <BrainCircuit className="w-3 h-3" /> Source Memories
                  </p>
                  <div className="grid grid-cols-1 gap-2">
                    {msg.sources.map((src, j) => (
                      <div key={j} className="bg-slate-900/50 border border-white/5 rounded-xl p-3 text-sm hover:border-blue-500/30 transition-colors">
                        <p className="text-slate-300 text-xs italic mb-2 line-clamp-2">"{src.text}"</p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-slate-500 font-mono px-2 py-0.5 rounded bg-white/5">{src.memory_type}</span>
                          <Link href={`/review/${src.meeting_id}`} className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium text-xs">
                            View Meeting <ArrowRight className="w-3 h-3" />
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0 border border-slate-600 mt-2">
                <User className="w-5 h-5 text-slate-300" />
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="flex gap-4 justify-start">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0 border border-blue-500/30 mt-2">
              <Bot className="w-5 h-5 text-blue-400" />
            </div>
            <div className="glass-panel rounded-2xl rounded-bl-none p-5 flex items-center gap-3 text-slate-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> 
              <span>Querying organizational memory...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleChat} className="relative group shrink-0">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="block w-full pl-6 pr-16 py-4 bg-slate-900/60 border border-white/10 rounded-2xl text-base text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all shadow-xl backdrop-blur-sm"
          placeholder="Ask a question about past decisions, discussions, or tasks..."
        />
        <button
          type="submit"
          disabled={!query.trim() || isTyping}
          className="absolute right-2 top-2 bottom-2 aspect-square bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:bg-slate-700 rounded-xl flex items-center justify-center transition-all text-white"
        >
          <Send className="w-5 h-5 ml-1" />
        </button>
      </form>
    </div>
  );
}
