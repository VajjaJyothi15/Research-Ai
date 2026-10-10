import React from 'react';
import { Sidebar } from './Sidebar';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#EDE9FE] text-[#334155] flex flex-col md:flex-row font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-[#E5E7F9]/50">
        <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
        <footer className="border-t border-[#C4B5FD] bg-[#DCD6FA] py-3.5 text-center text-xs text-[#334155]">
          ResAI v1.0 — Autonomous Evidence-Grounded Research Platform
        </footer>
      </div>
    </div>
  );
};
