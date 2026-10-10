import React, { useState } from 'react';
import { Settings as SettingsIcon, Cpu, Search, Save, ShieldCheck, ChevronDown, Lock, Zap } from 'lucide-react';

export const Settings: React.FC = () => {
  const [llmProvider, setLlmProvider] = useState('groq');
  const [searchProvider, setSearchProvider] = useState('ddg');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-[#312E81] flex items-center space-x-2.5">
          <SettingsIcon className="w-6 h-6 text-[#635BFF]" />
          <span>System Settings & Connections</span>
        </h1>
        <p className="text-[#334155] text-xs sm:text-sm mt-0.5">
          Configure AI model providers, search engines, and execution limits.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Setup Info */}
        <div className="bg-[#DCEBFF] border border-[#BFDBFE] rounded-xl p-5 space-y-1.5 shadow-xs">
          <h3 className="text-xs font-bold text-[#312E81] flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-[#635BFF]" />
            <span>How ResAI Providers Work</span>
          </h3>
          <p className="text-xs text-[#334155] leading-relaxed">
            ResAI orchestrates multi-agent research with Groq (Llama 3.3 70B), Google Gemini, or OpenAI. Real web search is executed via DuckDuckGo and OpenAlex academic papers (or Tavily API). Set your <code className="text-[#635BFF] font-mono">GROQ_API_KEY</code> in your backend <code className="text-[#635BFF] font-mono">.env</code> file. API keys remain securely on your server and are never exposed to the client.
          </p>
        </div>

        {/* AI Provider */}
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 space-y-4 shadow-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#312E81] flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-[#635BFF]" />
            <span>1. AI Model Provider</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div
              onClick={() => setLlmProvider('groq')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                llmProvider === 'groq'
                  ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                  : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
              }`}
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-[#312E81] flex items-center space-x-1">
                  <Zap className="w-3.5 h-3.5 text-[#635BFF]" />
                  <span>Groq (Recommended)</span>
                </h4>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#DDF7F0] text-[#0F9D91] font-mono border border-[#A7F3D0]">GROQ_API_KEY</span>
              </div>
              <p className="text-[11px] text-[#334155] mt-1 leading-snug">Ultra-fast Llama 3.3 70B inference for planning and report synthesis.</p>
            </div>

            <div
              onClick={() => setLlmProvider('gemini')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                llmProvider === 'gemini'
                  ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                  : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
              }`}
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-[#312E81]">Google Gemini</h4>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#E5E7F9] text-[#312E81] font-mono border border-[#C4B5FD]">GEMINI_API_KEY</span>
              </div>
              <p className="text-[11px] text-[#334155] mt-1 leading-snug">High-capacity reasoning with Google Gemini models.</p>
            </div>

            <div
              onClick={() => setLlmProvider('openai')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                llmProvider === 'openai'
                  ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                  : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
              }`}
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-[#312E81]">OpenAI (GPT-4o)</h4>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#E5E7F9] text-[#312E81] font-mono border border-[#C4B5FD]">OPENAI_API_KEY</span>
              </div>
              <p className="text-[11px] text-[#334155] mt-1 leading-snug">Structured completions and tool calling via OpenAI.</p>
            </div>
          </div>
        </div>

        {/* Web Search Provider */}
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 space-y-4 shadow-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#312E81] flex items-center space-x-2">
            <Search className="w-4 h-4 text-[#0F9D91]" />
            <span>2. Web Search & Retrieval Provider</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              onClick={() => setSearchProvider('ddg')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                searchProvider === 'ddg'
                  ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                  : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
              }`}
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-[#312E81]">DuckDuckGo + OpenAlex</h4>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#DDF7F0] text-[#0F9D91] font-semibold border border-[#A7F3D0]">Active</span>
              </div>
              <p className="text-[11px] text-[#334155] mt-1 leading-snug">Real web search paired with OpenAlex scholarly peer-reviewed papers.</p>
            </div>

            <div
              onClick={() => setSearchProvider('tavily')}
              className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                searchProvider === 'tavily'
                  ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                  : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
              }`}
            >
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-[#312E81]">Tavily Search API</h4>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#E5E7F9] text-[#312E81] font-mono border border-[#C4B5FD]">TAVILY_API_KEY</span>
              </div>
              <p className="text-[11px] text-[#334155] mt-1 leading-snug">Real-time search engine optimized for autonomous AI agents.</p>
            </div>
          </div>
        </div>

        {/* Collapsible Advanced Limits */}
        <details className="group bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-5 shadow-xs">
          <summary className="text-xs font-semibold text-[#312E81] cursor-pointer flex items-center justify-between list-none">
            <span className="flex items-center space-x-2">
              <Lock className="w-4 h-4 text-[#312E81]" />
              <span>Advanced Execution Safeguards & Limits</span>
            </span>
            <ChevronDown className="w-4 h-4 text-[#312E81]/60 group-open:rotate-180 transition-transform" />
          </summary>

          <div className="mt-3 space-y-2 pt-3 border-t border-[#C4B5FD] text-xs text-[#334155]">
            <p><strong>Tool Execution Budget:</strong> 15 calls per research run</p>
            <p><strong>Max Retrieved Sources:</strong> 10 canonical deduplicated domains</p>
            <p><strong>SSRF Protection:</strong> Enforced on all outgoing requests (private IP blocks barred)</p>
          </div>
        </details>

        <button
          type="submit"
          className="px-5 py-2.5 rounded-lg bg-[#635BFF] hover:bg-[#4F46E5] text-white font-semibold text-xs shadow-xs flex items-center space-x-2 transition-colors"
        >
          <Save className="w-4 h-4" />
          <span>{saved ? 'Settings Saved' : 'Save Connection Settings'}</span>
        </button>
      </form>
    </div>
  );
};
