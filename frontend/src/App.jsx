import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import UploadScreen from './components/UploadScreen';
import RequirementsScreen from './components/RequirementsScreen';
import ComplianceScreen from './components/ComplianceScreen';
import LoginScreen from './components/LoginScreen';
import { api } from './api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('tendercheck_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'requirements' | 'compliance'
  const officerId = currentUser?.officerId || 'OFFICER-7821';

  // Core Data State
  const [tenders, setTenders] = useState([]);
  const [selectedTender, setSelectedTender] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [loadingTenders, setLoadingTenders] = useState(true);
  const [loadingRequirements, setLoadingRequirements] = useState(false);
  const [loadingVendors, setLoadingVendors] = useState(false);
  const [appError, setAppError] = useState(null);

  // Load All Tenders
  const loadTenders = useCallback(async () => {
    setLoadingTenders(true);
    setAppError(null);
    try {
      const data = await api.getTenders();
      setTenders(data || []);
      // Do not auto-select prior results so the user starts with a clean upload state.
    } catch (err) {
      setAppError(`Unable to connect to TenderCheck backend: ${err.message}`);
    } finally {
      setLoadingTenders(false);
    }
  }, []);

  useEffect(() => {
    loadTenders();
  }, [loadTenders]);

  // Load Requirements for Selected Tender
  const loadRequirements = useCallback(async () => {
    if (!selectedTender) {
      setRequirements([]);
      return;
    }
    setLoadingRequirements(true);
    try {
      const data = await api.getRequirements(selectedTender.id);
      setRequirements(data || []);
    } catch (err) {
      // 425 means tender not yet parsed
      if (err.status !== 425) {
        console.error('Failed to load requirements', err);
      }
      setRequirements([]);
    } finally {
      setLoadingRequirements(false);
    }
  }, [selectedTender]);

  // Load Vendors for Selected Tender
  const loadVendors = useCallback(async () => {
    if (!selectedTender) {
      setVendors([]);
      return;
    }
    setLoadingVendors(true);
    try {
      const data = await api.getVendors(selectedTender.id);
      setVendors(data || []);
    } catch (err) {
      console.error('Failed to load vendors', err);
      setVendors([]);
    } finally {
      setLoadingVendors(false);
    }
  }, [selectedTender]);

  useEffect(() => {
    if (selectedTender) {
      loadRequirements();
      loadVendors();
    }
  }, [selectedTender, loadRequirements, loadVendors]);

  // Handle New Tender Upload
  const handleTenderCreated = async (newTender) => {
    await loadTenders();
    setSelectedTender(newTender);
    setActiveTab('requirements');
  };

  const [activeVendorForCompliance, setActiveVendorForCompliance] = useState('');

  // Tab navigation helper
  const handleNavigateToTab = (tabName, vendorName = null) => {
    if (vendorName) {
      setActiveVendorForCompliance(vendorName);
    }
    setActiveTab(tabName);
  };

  // Handle login / logout
  const handleLogin = (userData) => {
    setCurrentUser(userData);
    localStorage.setItem('tendercheck_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('tendercheck_user');
  };

  const totalDocumentsCount = vendors.reduce((acc, v) => acc + (v.document_count || 0), 0) + (selectedTender ? 1 : 0);

  if (!currentUser) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Institutional GovTech Header */}
      <Header
        tenders={tenders}
        selectedTender={selectedTender}
        onSelectTender={(t) => setSelectedTender(t)}
        officerId={officerId}
        onLogout={handleLogout}
      />

      {/* Global Error Banner if API is unreachable */}
      {appError && (
        <div
          style={{
            background: 'var(--status-fail-bg)',
            borderBottom: '1px solid var(--status-fail-border)',
            color: 'var(--status-fail-text)',
            padding: 'var(--space-1) var(--space-3)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>{appError}</span>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={loadTenders}
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Primary 3-Step Workflow Navigation */}
      <Navigation
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        counts={{
          documents: totalDocumentsCount,
          requirements: requirements.length,
          matches: requirements.length > 0 ? requirements.length : undefined,
        }}
      />

      {/* Main Body View */}
      <main className="main-content">
        {activeTab === 'upload' && (
          <UploadScreen
            tenders={tenders}
            selectedTender={selectedTender}
            onSelectTender={setSelectedTender}
            onTenderCreated={handleTenderCreated}
            vendors={vendors}
            onRefreshVendors={loadVendors}
            onNavigateToTab={handleNavigateToTab}
          />
        )}

        {activeTab === 'requirements' && (
          <RequirementsScreen
            selectedTender={selectedTender}
            requirements={requirements}
            loading={loadingRequirements}
            onRefreshRequirements={loadRequirements}
            onNavigateToCompliance={() => setActiveTab('compliance')}
          />
        )}

        {activeTab === 'compliance' && (
          <ComplianceScreen
            selectedTender={selectedTender}
            vendors={vendors}
            requirements={requirements}
            officerId={officerId}
            initialVendorName={activeVendorForCompliance}
          />
        )}
      </main>

      {/* Institutional GovTech Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          background: 'var(--bg-surface)',
          padding: 'var(--space-2) var(--space-3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: 'var(--text-muted)',
          marginTop: 'auto',
        }}
      >
        <div>
          Directorate of IT Procurement | TenderCheck Automated Compliance Verification System
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <span>Version: <strong>0.1.0 (GovTech Secure)</strong></span>
          <span style={{ color: 'var(--border-default)' }}>|</span>
          <span>Audit Status: <strong>Compliant (GFR 2017)</strong></span>
        </div>
      </footer>
    </div>
  );
}
