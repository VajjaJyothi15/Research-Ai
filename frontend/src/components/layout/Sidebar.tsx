import React, { useState } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import {
  BrainCircuit,
  Home,
  History,
  Database,
  Settings as SettingsIcon,
  PlusCircle,
  Menu,
  X,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { to: '/', label: 'Home', icon: Home, end: true },
    { to: '/history', label: 'My Research', icon: History, end: false },
    { to: '/sources', label: 'Sources', icon: Database, end: false },
    { to: '/settings', label: 'Settings', icon: SettingsIcon, end: false },
  ];

  const toggleMobile = () => setMobileOpen((prev) => !prev);
  const closeMobile = () => setMobileOpen(false);

  return (
    <>
      {/* Mobile Header Bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-[#DCD6FA] border-b border-[#C4B5FD] sticky top-0 z-40">
        <Link to="/" className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-[#635BFF] flex items-center justify-center text-white shadow-xs">
            <BrainCircuit className="w-4 h-4" />
          </div>
          <span className="font-bold text-base text-[#312E81]">
            Res<span className="text-[#635BFF]">AI</span>
          </span>
        </Link>
        <button
          onClick={toggleMobile}
          className="p-1.5 rounded-lg bg-[#E9E4FF] border border-[#C4B5FD] text-[#312E81] hover:bg-[#E5E7F9]"
          aria-label="Toggle navigation menu"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-[#312E81]/30 backdrop-blur-xs md:hidden"
          onClick={closeMobile}
        />
      )}

      {/* Sidebar Main Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-60 bg-[#DCD6FA] border-r border-[#C4B5FD] flex flex-col justify-between transition-transform duration-200 ease-in-out md:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-5 space-y-6">
          {/* Brand & App Info */}
          <div className="flex items-center justify-between">
            <Link to="/" onClick={closeMobile} className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#635BFF] flex items-center justify-center text-white shadow-xs">
                <BrainCircuit className="w-4 h-4" />
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-base text-[#312E81]">
                  Res<span className="text-[#635BFF]">AI</span>
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#E9E4FF] text-[#312E81] border border-[#C4B5FD] font-mono font-medium">
                  v1.0
                </span>
              </div>
            </Link>
          </div>

          {/* New Research CTA */}
          <Link
            to="/"
            onClick={closeMobile}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-[#635BFF] hover:bg-[#4F46E5] text-white shadow-xs transition-colors flex items-center justify-center space-x-1.5"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Research</span>
          </Link>

          {/* Navigation Links */}
          <nav className="space-y-1 pt-1">
            <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-[#312E81]/60">
              Workspace
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.end
                ? location.pathname === item.to
                : location.pathname.startsWith(item.to);

              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={closeMobile}
                  className={() =>
                    `flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-[#E9E4FF] text-[#312E81] font-semibold border border-[#C4B5FD] shadow-xs'
                        : 'text-[#334155] hover:text-[#312E81] hover:bg-[#E5E7F9]'
                    }`
                  }
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#635BFF]' : 'text-[#334155]'}`} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer Info */}
        <div className="p-4 border-t border-[#C4B5FD] text-[11px] text-[#334155]">
          <p className="font-semibold text-[#312E81]">Autonomous Evidence Agent</p>
          <p className="text-[10px] text-[#334155]/80 mt-0.5">Multi-source verification</p>
        </div>
      </aside>
    </>
  );
};
