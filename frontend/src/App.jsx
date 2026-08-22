import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Scanner from './components/Scanner';
import ResultCard from './components/ResultCard';
import HistoryDashboard from './components/HistoryDashboard';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ModelArchitecture from './components/ModelArchitecture';
import AdminDashboard from './components/AdminDashboard';
import AgentKitchenAssistant from './components/AgentKitchenAssistant';
import AuthModal from './components/AuthModal';
import { Leaf } from 'lucide-react';

const AppContent = () => {
  const [activeTab, setActiveTab] = useState('scanner'); // 'scanner', 'analytics', 'history', 'architecture', 'admin'
  const [scanResult, setScanResult] = useState(null);
  const { isAdmin } = useAuth();

  const handleScanComplete = (result) => {
    setScanResult(result);
  };

  const handleResetScan = () => {
    setScanResult(null);
    setActiveTab('scanner');
  };

  const handleViewHistory = () => {
    setScanResult(null);
    setActiveTab('history');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0b1120] text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white dark:selection:text-slate-950 transition-colors duration-200">
      
      {/* Top Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={(tab) => {
        setScanResult(null);
        setActiveTab(tab);
      }} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 space-y-8">
        {activeTab === 'scanner' && (
          <>
            {scanResult ? (
              <ResultCard
                result={scanResult}
                onReset={handleResetScan}
                onViewHistory={handleViewHistory}
              />
            ) : (
              <div className="space-y-8">
                <Scanner onScanComplete={handleScanComplete} />
                <AgentKitchenAssistant />
              </div>
            )}
          </>
        )}

        {activeTab === 'analytics' && <AnalyticsDashboard />}

        {activeTab === 'history' && (
          <div className="space-y-8">
            <HistoryDashboard />
            <AgentKitchenAssistant />
          </div>
        )}

        {activeTab === 'architecture' && <ModelArchitecture />}

        {activeTab === 'admin' && <AdminDashboard />}
      </main>

      {/* Auth Modal */}
      <AuthModal />

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-white/60 dark:bg-slate-950/60 py-8 text-center text-xs text-slate-500 dark:text-slate-500 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Leaf className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span className="font-semibold text-slate-800 dark:text-slate-300">Freshco AI</span>
            <span>— Smart Food Freshness, Agentic Zero-Waste Recipes & Analytics</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-500 dark:text-slate-400">
            <span>MobileNetV2 CNN</span>
            <span>•</span>
            <span>Agentic LLM Recipes</span>
            <span>•</span>
            <span>Role-Based Admin</span>
            <span>•</span>
            <span>OpenCV Vision</span>
            <span>•</span>
            <span>React + Vite</span>
          </div>
        </div>
      </footer>

    </div>
  );
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
