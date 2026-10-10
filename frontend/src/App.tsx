import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { NewResearch } from './pages/NewResearch';
import { ResearchWorkspace } from './pages/ResearchWorkspace';
import { ReportViewer } from './pages/ReportViewer';
import { EvidenceExplorer } from './pages/EvidenceExplorer';
import { ResearchHistory } from './pages/ResearchHistory';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new" element={<NewResearch />} />
            <Route path="/workspace/:id" element={<ResearchWorkspace />} />
            <Route path="/report/:id" element={<ReportViewer />} />
            <Route path="/sources" element={<EvidenceExplorer />} />
            <Route path="/explorer" element={<EvidenceExplorer />} />
            <Route path="/history" element={<ResearchHistory />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
