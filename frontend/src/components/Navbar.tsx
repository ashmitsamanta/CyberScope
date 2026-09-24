import React, { useState } from 'react';
import {
  ShieldAlert,
  LayoutDashboard,
  FolderGit2,
  Share2,
  Users,
  CreditCard,
  Target,
  Sparkles,
  Search,
  AlertCircle
} from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenSearch: () => void;
}

export const Navbar: React.FC<Props> = ({ activeTab, setActiveTab, onOpenSearch }) => {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'cases', label: 'Cases', icon: FolderGit2 },
    { id: 'graph', label: 'Fraud Graph', icon: Share2 },
    { id: 'entities', label: 'Entity Explorer', icon: Users },
    { id: 'transactions', label: 'Transactions', icon: CreditCard },
    { id: 'campaigns', label: 'Campaigns', icon: Target },
    { id: 'investigation', label: 'Workspace', icon: Sparkles, badge: 'DEMO' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#080C14]/90 backdrop-blur-md border-b border-cyber-border">
      <div className="max-w-[1720px] mx-auto px-4 lg:px-6 h-16 flex items-center justify-between">
        {/* Logo and Brand */}
        <div className="flex items-center gap-6">
          <div
            onClick={() => setActiveTab('dashboard')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-lg bg-cyber-accent/10 border border-cyber-accent/30 flex items-center justify-center text-cyber-accent group-hover:border-cyber-accent transition-colors shadow-[0_0_15px_rgba(6,182,212,0.2)]">
              <ShieldAlert className="w-5 h-5 text-cyber-accent" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold tracking-wider text-base text-slate-100 font-mono">
                  CYBER<span className="text-cyber-accent">SCOPE</span>
                </span>
                <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
                  v1.0-MVP
                </span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-tight font-sans">
                Explainable Cyber-Fraud Intelligence
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden xl:flex items-center gap-1 ml-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-cyber-card text-cyber-accent border border-cyber-border shadow-inner'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyber-accent' : 'text-slate-400'}`} />
                  {item.label}
                  {item.badge && (
                    <span className="ml-1 text-[9px] font-mono px-1.5 py-0.2 rounded bg-cyber-accent/20 text-cyber-accent border border-cyber-accent/40 animate-pulse">
                      {item.badge}
                    </span>
                  )}
                  {isActive && (
                    <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-cyber-accent rounded-full" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right action area */}
        <div className="flex items-center gap-3">
          {/* Natural Language Search Bar button */}
          <button
            onClick={onOpenSearch}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-cyber-surface border border-cyber-border text-slate-400 hover:text-slate-200 hover:border-slate-600 text-xs transition-all w-48 sm:w-64"
          >
            <Search className="w-3.5 h-3.5 text-cyber-accent" />
            <span className="truncate">Natural-language search...</span>
            <kbd className="ml-auto hidden sm:inline-block px-1.5 py-0.5 text-[9px] font-mono bg-slate-800 text-slate-400 rounded border border-slate-700">
              /
            </kbd>
          </button>

          {/* Defensive Synthetic Tag */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900/90 border border-slate-800 text-[11px] text-slate-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-slate-300">SYNTHETIC ENVIRONMENT</span>
          </div>
        </div>
      </div>

      {/* Mobile nav bar */}
      <div className="xl:hidden flex items-center justify-around border-t border-cyber-border py-2 px-2 bg-cyber-surface/90 overflow-x-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-1 px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap ${
                isActive ? 'text-cyber-accent font-semibold' : 'text-slate-400'
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
