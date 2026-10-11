import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Copy,
  ChevronDown,
  ChevronUp,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';
import type { ChatResponse, ExecutionTraceItem } from '../types';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  response?: ChatResponse;
  timestamp: string;
}

const SAMPLE_PROMPTS = [
  "Show customer CUST1001's account balance.",
  "Show the latest five transactions for CUST1002.",
  "Summarize CUST1001's spending this month.",
  "Analyze CUST1003 for suspicious transactions.",
  "Explain why transaction TXN4008 was flagged.",
  "Evaluate a simulated ₹500000 loan for CUST1001 over 36 months.",
  "Compare EMIs for ₹300000 and ₹500000 over 24 months.",
  "Check the simulated KYC status of CUST1004.",
  "Find the policy related to unusual transactions.",
  "Investigate CUST1001's transactions and loan eligibility."
];

interface AssistantPageProps {
  demoRole: string;
}

export const AssistantPage: React.FC<AssistantPageProps> = ({ demoRole }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-0',
      sender: 'assistant',
      text: "Hello! I am your AI Banking Operations Assistant powered by autonomous specialized agents. Ask me to query customer accounts, analyze spending, investigate suspicious transactions, evaluate simulated loans, or search compliance policies.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const resp: ChatResponse = await api.sendChatMessage(query, demoRole);
      const assistantMsg: Message = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: resp.answer,
        response: resp,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `Error processing request: ${err.message || 'Server error'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="h-[calc(100vh-8.5rem)] flex flex-col bg-navy-950 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      {/* Assistant Header */}
      <div className="px-6 py-3.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/30 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              Supervisor Orchestrator
              <span className="text-[10px] font-semibold bg-slate-800 text-teal-400 px-2 py-0.5 rounded-full border border-teal-500/20">
                DAG Control Plane
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">Coordinating Customer, Fraud, Credit, & Compliance Agents</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[11px] text-slate-500 block">Current Mode:</span>
          <span className="text-xs font-mono text-slate-300">Deterministic Fallback</span>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-6 py-2.5 bg-slate-950/60 border-b border-slate-800/80 overflow-x-auto flex gap-2 shrink-0 scrollbar-none">
        <span className="text-[11px] text-slate-500 flex items-center gap-1 font-medium shrink-0">
          <Sparkles className="w-3 h-3 text-teal-400" /> Suggestions:
        </span>
        {SAMPLE_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            className="text-[11px] text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 px-2.5 py-1 rounded-lg shrink-0 transition whitespace-nowrap"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-3xl ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                msg.sender === 'user'
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-800 border border-slate-700 text-teal-400'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className={`space-y-2 max-w-[85%] ${msg.sender === 'user' ? 'items-end' : ''}`}>
              <div
                className={`p-4 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-teal-600 text-white rounded-tr-none'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
                }`}
              >
                {/* Formatted Markdown Render for Assistant Text */}
                <div className="whitespace-pre-wrap">{msg.text}</div>

                {/* Response Metadata Badge */}
                {msg.response && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-teal-400">{msg.response.correlation_id}</span>
                      <span>•</span>
                      <span>Intent: <b className="text-slate-300">{msg.response.intent}</b></span>
                      <span>•</span>
                      <span>Agents: <b className="text-slate-300">{msg.response.agents_involved.join(', ')}</b></span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(msg.text)}
                      className="hover:text-white flex items-center gap-1 transition"
                      title="Copy response"
                    >
                      <Copy className="w-3 h-3" /> Copy
                    </button>
                  </div>
                )}
              </div>

              {/* Collapsible Execution Trace */}
              {msg.response && msg.response.trace && msg.response.trace.length > 0 && (
                <div className="bg-slate-950 border border-slate-800/80 rounded-xl overflow-hidden text-xs">
                  <button
                    onClick={() =>
                      setExpandedTraceId(expandedTraceId === msg.id ? null : msg.id)
                    }
                    className="w-full px-3 py-2 bg-slate-900/60 hover:bg-slate-900 flex items-center justify-between text-[11px] font-medium text-slate-400 hover:text-slate-200 transition"
                  >
                    <div className="flex items-center gap-1.5 text-teal-400">
                      <Cpu className="w-3.5 h-3.5" />
                      <span>Multi-Agent Execution Trace ({msg.response.trace.length} Steps)</span>
                    </div>
                    {expandedTraceId === msg.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  {expandedTraceId === msg.id && (
                    <div className="p-3 space-y-2 border-t border-slate-800/80">
                      {msg.response.trace.map((step: ExecutionTraceItem, sIdx: number) => (
                        <div
                          key={sIdx}
                          className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] space-y-1 font-mono"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-teal-400 font-semibold">{step.phase}</span>
                            <span className="text-slate-500">{step.duration_ms}ms</span>
                          </div>
                          {step.agent_name && (
                            <div className="text-slate-300">
                              Agent: <span className="text-white font-medium">{step.agent_name}</span>
                            </div>
                          )}
                          {step.output_data && (
                            <pre className="text-[10px] text-slate-400 bg-slate-950 p-1.5 rounded overflow-x-auto max-h-24">
                              {JSON.stringify(step.output_data, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <span className="text-[10px] text-slate-500 block px-1">{msg.timestamp}</span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 max-w-xl animate-pulse">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-teal-400 shrink-0">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-4 rounded-2xl rounded-tl-none bg-slate-900 border border-slate-800 text-xs text-slate-400 space-y-1">
              <p className="font-semibold text-slate-300 flex items-center gap-2">
                <span>Supervisor decomposing plan & executing specialized agents...</span>
              </p>
              <p className="text-[11px] text-slate-500 font-mono">Running database queries & tool evaluations</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center gap-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything: e.g. 'Investigate CUST1001' or 'Evaluate ₹500000 loan for CUST1001'..."
          disabled={loading}
          className="flex-1 bg-slate-950 border border-slate-800 focus:border-teal-500 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition shadow-inner"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-navy-950 font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-lg shadow-teal-500/20 shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
};
