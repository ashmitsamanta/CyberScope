import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { SearchModal } from './components/SearchModal';
import { DashboardPage } from './pages/DashboardPage';
import { CasesPage } from './pages/CasesPage';
import { GraphPage } from './pages/GraphPage';
import { EntityExplorerPage } from './pages/EntityExplorerPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { InvestigationWorkspacePage } from './pages/InvestigationWorkspacePage';
import { ShieldCheck, Info } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<number>(1);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);

  const handleSelectCase = (caseId: number) => {
    setSelectedCaseId(caseId);
    setActiveTab('investigation');
  };

  return (
    <div className="min-h-screen bg-cyber-bg text-slate-100 flex flex-col font-sans">
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenSearch={() => setIsSearchOpen(true)}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 lg:p-6 pb-16">
        {activeTab === 'dashboard' && (
          <DashboardPage
            onSelectCase={handleSelectCase}
            onNavigateTab={setActiveTab}
          />
        )}

        {activeTab === 'cases' && (
          <CasesPage onSelectCase={handleSelectCase} />
        )}

        {activeTab === 'graph' && (
          <GraphPage onSelectCase={handleSelectCase} />
        )}

        {activeTab === 'entities' && (
          <EntityExplorerPage onSelectCase={handleSelectCase} />
        )}

        {activeTab === 'transactions' && (
          <TransactionsPage onSelectCase={handleSelectCase} />
        )}

        {activeTab === 'campaigns' && (
          <CampaignsPage onSelectCase={handleSelectCase} />
        )}

        {activeTab === 'investigation' && (
          <InvestigationWorkspacePage
            caseId={selectedCaseId}
            onSelectCase={handleSelectCase}
          />
        )}
      </main>

      {/* Natural Language Controlled Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectCase={handleSelectCase}
      />

      {/* Mandatory Safety & Scope Disclaimer Footer */}
      <footer className="fixed bottom-0 left-0 right-0 z-40 bg-[#060911]/95 backdrop-blur-md border-t border-cyber-border py-1.5 px-4 text-center">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-[10px] font-mono text-slate-400">
          <Info className="w-3 h-3 text-cyber-accent flex-shrink-0" />
          <span>
            <strong>DEFENSIVE SCOPE NOTICE:</strong> CYBERSCOPE is a defensive research and hackathon prototype using synthetic data. Risk scores are investigative signals, not proof of criminal activity.
          </span>
        </div>
      </footer>
    </div>
  );
}

export default App;
