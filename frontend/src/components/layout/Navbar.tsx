import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { BrainCircuit, Home, History, Database, Settings as SettingsIcon, PlusCircle } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 glass-card border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <BrainCircuit className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-bold text-lg text-white tracking-wide">Res<span className="text-sky-400">AI</span></span>
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-sky-950/80 text-sky-400 border border-sky-800 font-mono">v1.0</span>
          </div>
        </Link>

        <nav className="flex items-center space-x-1 sm:space-x-2">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`
            }
          >
            <Home className="w-4 h-4" />
            <span>Home</span>
          </NavLink>

          <NavLink
            to="/history"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`
            }
          >
            <History className="w-4 h-4" />
            <span>My Research</span>
          </NavLink>

          <NavLink
            to="/sources"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`
            }
          >
            <Database className="w-4 h-4" />
            <span>Sources</span>
          </NavLink>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`
            }
          >
            <SettingsIcon className="w-4 h-4" />
            <span>Settings</span>
          </NavLink>

          <NavLink
            to="/new"
            className="ml-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium bg-sky-600 hover:bg-sky-500 text-white shadow-md shadow-sky-600/30 transition-all flex items-center space-x-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Start New Research</span>
          </NavLink>
        </nav>
      </div>
    </header>
  );
};
