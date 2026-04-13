import React, { useState, useEffect } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import JobFeed from './pages/JobFeed';
import ApplicationTracker from './pages/ApplicationTracker';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import Resources from './pages/Resources';
import Community from './pages/Community';
import { checkHealth, setBackendPort, updateBaseURL } from './api';
import { Loader2, ServerCrash } from 'lucide-react';

function App() {
  const [backendReady, setBackendReady] = useState(false);
  const [checking, setChecking] = useState(true);
  const [currentPort, setCurrentPort] = useState(8000);

  useEffect(() => {
    let interval;
    let retries = 0;
    const maxRetries = 15;
    
    const initAndVerify = async () => {
      // 1. First, check if we're in Electron and need to discover the port
      if (window.electronAPI && window.electronAPI.getBackendConfig) {
        try {
          const config = await window.electronAPI.getBackendConfig();
          if (config && config.port) {
            console.log(`[App] Discovered backend port: ${config.port}`);
            setBackendPort(config.port);
            setCurrentPort(config.port);
            updateBaseURL(); // Update axios baseURL with the new port
          }
        } catch (err) {
          console.error('[App] Failed to fetch backend config:', err);
        }
      }

      // 2. Then proceed with the health verification

      const verifyHealth = async () => {
        const isHealthy = await checkHealth();
        if (isHealthy) {
          setBackendReady(true);
          setChecking(false);
          if (interval) clearInterval(interval);
        } else {
          retries++;
          if (retries >= maxRetries) {
            setChecking(false); // Give up after 30 seconds
            if (interval) clearInterval(interval);
          }
          // Keep checking = true while retrying
        }
      };

      await verifyHealth();

      if (!backendReady && retries < maxRetries) {
        interval = setInterval(verifyHealth, 2000);
      }
    };

    initAndVerify();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  if (!backendReady) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col items-center justify-center p-4">
        <div className="bg-[var(--bg-secondary)] p-8 rounded-2xl shadow-2xl border border-[var(--border)] max-w-md w-full text-center space-y-6">
          <div className="w-16 h-16 bg-[var(--accent-subtle)] rounded-full flex items-center justify-center mx-auto mb-4">
            {checking ? (
              <Loader2 className="w-8 h-8 text-[var(--accent)] animate-spin" />
            ) : (
              <ServerCrash className="w-8 h-8 text-[var(--danger)]" />
            )}
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            {checking ? 'Connecting to InternIQ...' : 'Waiting for Backend...'}
          </h1>
          <p className="text-[var(--text-secondary)]">
            {checking
              ? 'Verifying database connection...'
              : `The frontend is ready, but it cannot reach the backend server (localhost:${currentPort}). Please ensure your Python backend is running.`}
          </p>
          {!checking && (
            <div className="animate-pulse flex items-center justify-center gap-2 text-sm text-[var(--accent)] font-medium">
              <Loader2 className="w-4 h-4 animate-spin" /> Retrying automatically...
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="h-screen bg-[var(--bg-primary)] flex overflow-hidden">
        {/* Fixed Navbar on the left */}
        <aside className="w-64 flex-shrink-0 h-full">
          <Navbar />
        </aside>
        
        {/* Main Content Area */}
        <main className="flex-1 h-full overflow-y-auto bg-[var(--bg-primary)]">
          <Routes>
            <Route path="/" element={<JobFeed />} />
            <Route path="/tracker" element={<ApplicationTracker />} />
            <Route path="/resources" element={<Resources />} />
            <Route path="/community" element={<Community />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
