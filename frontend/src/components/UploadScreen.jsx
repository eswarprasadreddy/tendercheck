import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileCheck,
  FileUp,
  AlertCircle,
  Building,
  CheckCircle2,
  RefreshCw,
  FolderOpen,
  ArrowRight,
  Check,
  X,
  FileText,
} from 'lucide-react';
import { api } from '../api';

const DEMO_TENDER = {
  title: 'Supply & Installation of 120 Enterprise Laptops for Directorate of IT',
  reference: 'GEM/2026/B/8821941',
  file: 'tender_gem_2026_it_hardware.pdf',
};

const DEMO_CATALOG = {
  vendor_a: {
    vendorName: 'Vendor A (Apex Tech Solutions Pvt Ltd)',
    shortName: 'Vendor A',
    docs: {
      technical_bid: {
        file: 'vendor_a/vendor_a_technical_bid_and_specs.pdf',
        name: 'vendor_a_technical_bid_and_specs.pdf',
        label: 'Technical Bid & Specs (Core i7, 16GB RAM, 512GB SSD, 14")',
        type: 'technical_bid',
      },
      financials: {
        file: 'vendor_a/vendor_a_profile_and_financials.pdf',
        name: 'vendor_a_profile_and_financials.pdf',
        label: 'Audited Financials (Annual Turnover ₹3.40 Cr, 5 Yrs Exp)',
        type: 'financials',
      },
      certifications: {
        file: 'vendor_a/vendor_a_compliance_and_certifications.pdf',
        name: 'vendor_a_compliance_and_certifications.pdf',
        label: 'Certifications (ISO 9001:2015, BIS CRS, GST, MAF)',
        type: 'certifications',
      },
      company_profile: {
        file: 'vendor_a/vendor_a_profile_and_financials.pdf',
        name: 'vendor_a_profile_and_financials.pdf',
        label: 'Company Profile & Govt Experience Record',
        type: 'company_profile',
      },
      other: {
        file: 'vendor_a/vendor_a_technical_bid_and_specs.pdf',
        name: 'vendor_a_technical_bid_and_specs.pdf',
        label: 'Supporting Technical Bid Annexure',
        type: 'other',
      },
    },
  },
  vendor_b: {
    vendorName: 'Vendor B (Nexura Hardware Systems Ltd)',
    shortName: 'Vendor B',
    docs: {
      technical_bid: {
        file: 'vendor_b/vendor_b_technical_bid.pdf',
        name: 'vendor_b_technical_bid.pdf',
        label: 'Technical Bid (Ryzen 7, 16GB RAM, 512GB SSD)',
        type: 'technical_bid',
      },
      financials: {
        file: 'vendor_b/vendor_b_financials_and_compliance.pdf',
        name: 'vendor_b_financials_and_compliance.pdf',
        label: 'Financials & Tax Compliance (Turnover ₹2.85 Cr)',
        type: 'financials',
      },
      company_profile: {
        file: 'vendor_b/vendor_b_company_profile.pdf',
        name: 'vendor_b_company_profile.pdf',
        label: 'Company Profile & Past Govt Orders',
        type: 'company_profile',
      },
      certifications: {
        file: 'vendor_b/vendor_b_financials_and_compliance.pdf',
        name: 'vendor_b_financials_and_compliance.pdf',
        label: 'Compliance Registrations & Certifications',
        type: 'certifications',
      },
      other: {
        file: 'vendor_b/vendor_b_technical_bid.pdf',
        name: 'vendor_b_technical_bid.pdf',
        label: 'Supporting Technical Bid Annexure',
        type: 'other',
      },
    },
  },
};

const PRESET_BUTTONS = [
  { vendorKey: 'vendor_a', type: 'technical_bid', label: 'Vendor A - Technical Bid', badge: 'Core i7 / 512GB SSD' },
  { vendorKey: 'vendor_a', type: 'financials', label: 'Vendor A - Financials', badge: 'Turnover 3.40 Cr' },
  { vendorKey: 'vendor_a', type: 'certifications', label: 'Vendor A - Certifications', badge: 'ISO 9001 / BIS / MAF' },
  { vendorKey: 'vendor_b', type: 'technical_bid', label: 'Vendor B - Technical Bid', badge: 'Ryzen 7 / 512GB SSD' },
  { vendorKey: 'vendor_b', type: 'financials', label: 'Vendor B - Financials', badge: 'Turnover 2.85 Cr' },
  { vendorKey: 'vendor_b', type: 'company_profile', label: 'Vendor B - Profile', badge: '4 Yrs Experience' },
];

async function getDemoFile(path) {
  const response = await fetch(`/demo_data/${path}`);
  if (!response.ok) throw new Error(`Could not load bundled demo PDF at /demo_data/${path}`);
  const blob = await response.blob();
  return new File([blob], path.split('/').pop(), { type: 'application/pdf' });
}

export default function UploadScreen({
  tenders,
  selectedTender,
  onSelectTender,
  onTenderCreated,
  vendors,
  onRefreshVendors,
  onNavigateToTab,
}) {
  // Tender Upload Form State
  const [tenderTitle, setTenderTitle] = useState('');
  const [tenderRef, setTenderRef] = useState('');
  const [tenderFile, setTenderFile] = useState(null);
  const [uploadingTender, setUploadingTender] = useState(false);
  const [tenderError, setTenderError] = useState(null);
  const [tenderSuccess, setTenderSuccess] = useState(null);
  const [loadingDemoTender, setLoadingDemoTender] = useState(false);

  // Vendor Doc Upload Form State - default to clean empty state
  const [vendorName, setVendorName] = useState('');
  const [docType, setDocType] = useState('technical_bid');
  const [vendorFile, setVendorFile] = useState(null);
  const [uploadingVendorDoc, setUploadingVendorDoc] = useState(false);
  const [vendorDocError, setVendorDocError] = useState(null);
  const [vendorDocSuccess, setVendorDocSuccess] = useState(null);
  const [loadingDemoDocument, setLoadingDemoDocument] = useState(false);
  const [autoAttachDemoPdf, setAutoAttachDemoPdf] = useState(false);

  // Batch demo ingestion state
  const [batchIngesting, setBatchIngesting] = useState(false);
  const [batchProgress, setBatchProgress] = useState('');

  // Helper to resolve vendor key
  const getVendorKey = (name) => {
    if (!name) return 'vendor_a';
    const lower = name.toLowerCase();
    if (lower.includes('nexura') || lower.includes('vendor b')) {
      return 'vendor_b';
    }
    return 'vendor_a';
  };

  // Helper to attach demo file for a given vendor and docType
  const attachDemoFile = async (vName, type) => {
    const vKey = getVendorKey(vName);
    const catalog = DEMO_CATALOG[vKey];
    const docInfo = catalog.docs[type] || catalog.docs.technical_bid;

    setLoadingDemoDocument(true);
    setVendorDocError(null);
    try {
      const file = await getDemoFile(docInfo.file);
      setVendorFile(file);
      setVendorDocSuccess(`Sample PDF '${docInfo.name}' attached for ${catalog.shortName} (${type.replace('_', ' ')}).`);
    } catch (err) {
      setVendorDocError(err.message || 'Failed to fetch demo PDF.');
    } finally {
      setLoadingDemoDocument(false);
    }
  };

  // When docType changes in dropdown: automatically load and attach corresponding demo PDF
  const handleDocTypeChange = async (newType) => {
    setDocType(newType);
    if (autoAttachDemoPdf) {
      let currentVendor = vendorName;
      if (!currentVendor || !currentVendor.trim()) {
        currentVendor = DEMO_CATALOG.vendor_a.vendorName;
        setVendorName(currentVendor);
      }
      await attachDemoFile(currentVendor, newType);
    }
  };

  // When vendor name is chosen from quick pills
  const handleVendorSelect = async (newVendorName) => {
    setVendorName(newVendorName);
    if (autoAttachDemoPdf) {
      await attachDemoFile(newVendorName, docType);
    }
  };

  // 1-Click Quick Fill from preset chips
  const handleQuickPreset = async (preset) => {
    const vConfig = DEMO_CATALOG[preset.vendorKey];
    setVendorName(vConfig.vendorName);
    setDocType(preset.type);
    await attachDemoFile(vConfig.vendorName, preset.type);
  };

  // Quick fill demo tender (NIT)
  const fillDemoTender = async () => {
    setTenderError(null);
    setTenderSuccess(null);

    // If the sample tender is already in the database, activate it directly and navigate to Extracted Requirements
    const existing = tenders?.find((t) => t.reference_number === DEMO_TENDER.reference);
    if (existing && onSelectTender) {
      onSelectTender(existing);
      setTenderSuccess(`Sample tender '${DEMO_TENDER.reference}' is active. Showing extracted requirements.`);
      if (onNavigateToTab) {
        onNavigateToTab('requirements');
      }
      return;
    }

    setLoadingDemoTender(true);
    try {
      const file = await getDemoFile(DEMO_TENDER.file);
      setTenderTitle(DEMO_TENDER.title);
      setTenderRef(DEMO_TENDER.reference);
      setTenderFile(file);
      setTenderSuccess(`Sample NIT PDF '${DEMO_TENDER.file}' attached and form pre-filled. Click 'Ingest & Extract Tender Requirements' below.`);
    } catch (err) {
      setTenderError(err.message || 'Failed to load demo tender.');
    } finally {
      setLoadingDemoTender(false);
    }
  };

  // Handle Tender Upload
  const handleTenderUpload = async (e) => {
    e.preventDefault();
    if (!tenderFile || !tenderTitle.trim() || !tenderRef.trim()) {
      setTenderError('Please provide tender title, reference number, and a PDF file.');
      return;
    }
    setTenderError(null);
    setTenderSuccess(null);
    setUploadingTender(true);

    try {
      const formData = new FormData();
      formData.append('file', tenderFile);
      formData.append('title', tenderTitle.trim());
      formData.append('reference_number', tenderRef.trim());

      const res = await api.uploadTender(formData);
      setTenderSuccess(`Tender uploaded successfully with Reference: ${res.reference_number}`);
      setTenderTitle('');
      setTenderRef('');
      setTenderFile(null);
      if (onTenderCreated) onTenderCreated(res);
    } catch (err) {
      setTenderError(err.message || 'Failed to upload tender document.');
    } finally {
      setUploadingTender(false);
    }
  };

  // Handle Vendor Document Upload
  const handleVendorDocUpload = async (e) => {
    e.preventDefault();
    if (!selectedTender) {
      setVendorDocError('Please select or upload a tender first.');
      return;
    }
    if (!vendorFile || !vendorName.trim()) {
      setVendorDocError('Please provide vendor name and select a PDF file.');
      return;
    }
    setVendorDocError(null);
    setVendorDocSuccess(null);
    setUploadingVendorDoc(true);

    try {
      const formData = new FormData();
      formData.append('file', vendorFile);
      formData.append('vendor_name', vendorName.trim());
      if (docType) formData.append('doc_type', docType);

      const res = await api.uploadVendorDocument(selectedTender.id, formData);
      setVendorDocSuccess(`Document '${res.original_filename}' uploaded for ${res.vendor_name}`);
      setVendorFile(null);
      if (onRefreshVendors) onRefreshVendors();
    } catch (err) {
      setVendorDocError(err.message || 'Failed to upload vendor document.');
    } finally {
      setUploadingVendorDoc(false);
    }
  };

  // Individual Vendor Ingestion & Evaluation
  const handleIngestVendor = async (vendorKey) => {
    if (!selectedTender) {
      setVendorDocError('Please select or upload a tender first.');
      return;
    }
    const vConfig = DEMO_CATALOG[vendorKey];
    setBatchIngesting(true);
    setVendorDocError(null);
    setVendorDocSuccess(null);

    const docItems = [
      vConfig.docs.technical_bid,
      vConfig.docs.financials,
      vConfig.docs.certifications || vConfig.docs.company_profile,
    ].filter(Boolean);

    try {
      for (let i = 0; i < docItems.length; i++) {
        const item = docItems[i];
        setBatchProgress(`Uploading ${i + 1}/${docItems.length} for ${vConfig.shortName}: ${item.name}...`);
        const file = await getDemoFile(item.file);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('vendor_name', vConfig.vendorName);
        formData.append('doc_type', item.type);
        await api.uploadVendorDocument(selectedTender.id, formData);
      }
      setBatchProgress(`Evaluating ${vConfig.shortName} against tender requirements...`);
      await api.runMatching(selectedTender.id, vConfig.vendorName);
      if (onRefreshVendors) await onRefreshVendors();
      setVendorDocSuccess(`Successfully uploaded and evaluated ${vConfig.shortName}. Navigating to report...`);
      if (onNavigateToTab) {
        onNavigateToTab('compliance', vConfig.vendorName);
      }
    } catch (err) {
      setVendorDocError(`Error processing ${vConfig.shortName}: ${err.message || 'Unknown error'}`);
    } finally {
      setBatchIngesting(false);
      setBatchProgress('');
    }
  };

  return (
    <div>
      {/* Testing Utilities (Discreet & Professional) */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-2) var(--space-3)',
          marginBottom: 'var(--space-3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
        }}
      >
        <div>
          <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
            Procurement Testing Tools (Optional)
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Step 1: Load sample tender to inspect requirements. Step 2: Ingest Vendor A or Vendor B to verify compliance reports.
          </div>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={fillDemoTender}
            disabled={loadingDemoTender || uploadingTender}
            style={{ fontSize: '11px' }}
          >
            <FileUp size={12} />
            <span>{loadingDemoTender ? 'Loading...' : 'Pre-fill Sample NIT (Tender)'}</span>
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleIngestVendor('vendor_a')}
            disabled={!selectedTender || batchIngesting}
            style={{ fontSize: '11px' }}
          >
            <Building size={12} />
            <span>{batchIngesting ? batchProgress || 'Processing...' : 'Upload & Evaluate Vendor A'}</span>
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => handleIngestVendor('vendor_b')}
            disabled={!selectedTender || batchIngesting}
            style={{ fontSize: '11px' }}
          >
            <Building size={12} />
            <span>{batchIngesting ? batchProgress || 'Processing...' : 'Upload & Evaluate Vendor B'}</span>
          </button>
        </div>
      </div>

      {/* Active Tender Banner */}
      {selectedTender ? (
        <div
          className="gov-card"
          style={{
            borderLeft: '4px solid var(--accent-primary)',
            padding: 'var(--space-2) var(--space-3)',
            marginBottom: 'var(--space-3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Active Tender Under Evaluation
            </div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
              {selectedTender.title}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Reference Number: <strong>{selectedTender.reference_number}</strong> | Status: <strong>{selectedTender.status}</strong> | Pages: <strong>{selectedTender.page_count || 3}</strong>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => onNavigateToTab('requirements')}
          >
            <span>View Extracted Requirements</span>
            <ArrowRight size={14} />
          </button>
        </div>
      ) : (
        <div
          className="gov-card"
          style={{
            borderLeft: '4px solid var(--border-default)',
            padding: 'var(--space-2) var(--space-3)',
            marginBottom: 'var(--space-3)',
          }}
        >
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
            No Tender Selected
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Please upload a tender document below or click "Pre-fill Demo Tender (NIT)" to ingest the sample IT Hardware tender.
          </div>
        </div>
      )}

      {/* Two Column Upload Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
        {/* Tender Upload Card */}
        <div className="gov-card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <div className="card-title">
                <FileUp size={16} style={{ color: 'var(--accent-primary)' }} />
                <span>Upload Tender Document</span>
              </div>
              <div className="card-subtitle">
                Official GeM / Government tender Notice Inviting Tender (NIT) PDF
              </div>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={fillDemoTender}
              disabled={loadingDemoTender || uploadingTender}
            >
              <FileCheck size={13} />
              <span>{loadingDemoTender ? 'Loading...' : 'Pre-fill Sample NIT'}</span>
            </button>
          </div>
          <div className="card-body">
            {tenderError && (
              <div
                className="status-badge fail"
                style={{
                  width: '100%',
                  marginBottom: 'var(--space-2)',
                  padding: '8px var(--space-2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertCircle size={14} />
                  <span>{tenderError}</span>
                </div>
                {tenders?.find((t) => t.reference_number === tenderRef.trim()) && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '11px', padding: '3px 8px', borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}
                    onClick={() => {
                      const match = tenders.find((t) => t.reference_number === tenderRef.trim());
                      if (match && onSelectTender) {
                        onSelectTender(match);
                        setTenderError(null);
                        setTenderSuccess(`Tender '${match.reference_number}' is now the Active Tender.`);
                      }
                    }}
                  >
                    Select as Active Tender
                  </button>
                )}
              </div>
            )}
            {tenderSuccess && (
              <div className="status-badge pass" style={{ width: '100%', marginBottom: 'var(--space-2)', padding: '6px var(--space-1)' }}>
                <CheckCircle2 size={14} />
                <span>{tenderSuccess}</span>
              </div>
            )}

            <form onSubmit={handleTenderUpload}>
              <div className="form-group">
                <label className="form-label" htmlFor="tender-ref">
                  Tender Reference / Bid Number *
                </label>
                <input
                  id="tender-ref"
                  type="text"
                  className="form-input"
                  placeholder="e.g. GEM/2026/B/8821941"
                  value={tenderRef}
                  onChange={(e) => setTenderRef(e.target.value)}
                  disabled={uploadingTender}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="tender-title">
                  Tender Title / Description *
                </label>
                <input
                  id="tender-title"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Supply & Installation of Enterprise Laptops"
                  value={tenderTitle}
                  onChange={(e) => setTenderTitle(e.target.value)}
                  disabled={uploadingTender}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="tender-file">
                  Tender PDF Document *
                </label>
                <input
                  id="tender-file"
                  type="file"
                  accept=".pdf"
                  className="form-input"
                  onChange={(e) => setTenderFile(e.target.files[0] || null)}
                  disabled={uploadingTender}
                />

                {tenderFile ? (
                  <div className="file-attached-card">
                    <div className="file-attached-info">
                      <FileCheck size={18} className="file-attached-icon" />
                      <div>
                        <div className="file-attached-name">{tenderFile.name}</div>
                        <div className="file-attached-desc">
                          {(tenderFile.size / 1024).toFixed(1)} KB | Official tender document attached and ready for extraction
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setTenderFile(null)}
                      style={{ padding: '2px 8px' }}
                    >
                      <X size={12} />
                      <span>Remove</span>
                    </button>
                  </div>
                ) : (
                  <div className="form-hint">Only official PDF format is accepted. Click 'Pre-fill Sample NIT' to use the bundled sample.</div>
                )}
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: 'var(--space-1)' }}
                disabled={uploadingTender}
              >
                {uploadingTender ? (
                  <>
                    <RefreshCw size={14} className="spinner" />
                    <span>Processing Tender Document...</span>
                  </>
                ) : (
                  <>
                    <Upload size={14} />
                    <span>Ingest & Extract Tender Requirements</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Vendor Documents Upload Card */}
        <div className="gov-card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div>
              <div className="card-title">
                <Building size={16} style={{ color: 'var(--accent-primary)' }} />
                <span>Upload Vendor Bid Documents</span>
              </div>
              <div className="card-subtitle">
                Technical bids, audited balance sheets, ISO/BIS certificates, MAF
              </div>
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', cursor: 'pointer', color: 'var(--text-secondary)' }}>
              <input
                type="checkbox"
                checked={autoAttachDemoPdf}
                onChange={(e) => setAutoAttachDemoPdf(e.target.checked)}
              />
              <span>Auto-load Demo PDF on type change</span>
            </label>
          </div>

          <div className="card-body">
            {/* Quick Fill Document Presets */}
            <div style={{ marginBottom: 'var(--space-2)' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Quick-Fill Document Presets (Pre-fills all text + attaches PDF):
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {PRESET_BUTTONS.map((p) => {
                  const isCurrent =
                    getVendorKey(vendorName) === p.vendorKey && docType === p.type && vendorFile !== null;
                  return (
                    <button
                      key={`${p.vendorKey}_${p.type}`}
                      type="button"
                      className={`btn btn-secondary btn-sm ${isCurrent ? 'active' : ''}`}
                      style={{
                        fontSize: '11px',
                        padding: '3px 8px',
                        borderColor: isCurrent ? 'var(--accent-primary)' : undefined,
                        background: isCurrent ? 'var(--accent-subtle)' : undefined,
                      }}
                      onClick={() => handleQuickPreset(p)}
                      disabled={!selectedTender || uploadingVendorDoc || loadingDemoDocument}
                    >
                      <FileText size={11} style={{ color: 'var(--accent-primary)' }} />
                      <span>{p.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {vendorDocError && (
              <div className="status-badge fail" style={{ width: '100%', marginBottom: 'var(--space-2)', padding: '6px var(--space-1)' }}>
                <AlertCircle size={14} />
                <span>{vendorDocError}</span>
              </div>
            )}
            {vendorDocSuccess && (
              <div className="status-badge pass" style={{ width: '100%', marginBottom: 'var(--space-2)', padding: '6px var(--space-1)' }}>
                <CheckCircle2 size={14} />
                <span>{vendorDocSuccess}</span>
              </div>
            )}

            <form onSubmit={handleVendorDocUpload}>
              <div className="form-group">
                <label className="form-label" htmlFor="vendor-name">
                  Vendor / Bidder Legal Name *
                </label>
                <input
                  id="vendor-name"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Vendor A (Apex Tech Solutions Pvt Ltd)"
                  value={vendorName}
                  onChange={(e) => {
                    setVendorName(e.target.value);
                  }}
                  disabled={uploadingVendorDoc || !selectedTender}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Quick vendor select:</span>
                  <button
                    type="button"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-primary)',
                      textDecoration: 'underline',
                      cursor: 'pointer',
                      fontSize: '11px',
                      padding: 0,
                      fontWeight: getVendorKey(vendorName) === 'vendor_a' ? 700 : 400,
                    }}
                    onClick={() => handleVendorSelect(DEMO_CATALOG.vendor_a.vendorName)}
                  >
                    Vendor A (Apex Tech)
                  </button>
                  <span style={{ color: 'var(--border-default)', margin: '0 4px' }}>|</span>
                  <button
                    type="button"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-primary)',
                      textDecoration: 'underline',
                      cursor: 'pointer',
                      fontSize: '11px',
                      padding: 0,
                      fontWeight: getVendorKey(vendorName) === 'vendor_b' ? 700 : 400,
                    }}
                    onClick={() => handleVendorSelect(DEMO_CATALOG.vendor_b.vendorName)}
                  >
                    Vendor B (Nexura)
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="doc-type">
                  Document Category / Type * (Changing this auto-attaches demo PDF)
                </label>
                <select
                  id="doc-type"
                  className="form-select"
                  value={docType}
                  onChange={(e) => handleDocTypeChange(e.target.value)}
                  disabled={uploadingVendorDoc || !selectedTender}
                >
                  <option value="technical_bid">Technical Bid & Hardware Specifications</option>
                  <option value="financials">Financials & Balance Sheet (Turnover)</option>
                  <option value="certifications">ISO / BIS / GST Registrations & Certs</option>
                  <option value="company_profile">Company Profile & Past Orders</option>
                  <option value="other">Other Supporting Tender Annexure</option>
                </select>
                <div className="form-hint" style={{ marginTop: '2px' }}>
                  {autoAttachDemoPdf ? (
                    <span style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>
                      Auto-load sample PDF enabled: selecting a category loads the matching sample document.
                    </span>
                  ) : (
                    <span>Auto-load is disabled. Select a file manually below or enable the checkbox above.</span>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="vendor-file">
                  Vendor Document PDF *
                </label>
                <input
                  id="vendor-file"
                  type="file"
                  accept=".pdf"
                  className="form-input"
                  onChange={(e) => setVendorFile(e.target.files[0] || null)}
                  disabled={uploadingVendorDoc || !selectedTender}
                />

                {loadingDemoDocument && (
                  <div style={{ fontSize: '12px', color: 'var(--accent-primary)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <RefreshCw size={12} className="spinner" />
                    <span>Loading demo PDF for selected document type...</span>
                  </div>
                )}

                {vendorFile && !loadingDemoDocument && (
                  <div className="file-attached-card">
                    <div className="file-attached-info">
                      <FileCheck size={18} className="file-attached-icon" />
                      <div>
                        <div className="file-attached-name">{vendorFile.name}</div>
                        <div className="file-attached-desc">
                          {(vendorFile.size / 1024).toFixed(1)} KB | Attached for {vendorName || 'Selected Vendor'} ({docType.replace('_', ' ')})
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setVendorFile(null)}
                      style={{ padding: '2px 8px' }}
                    >
                      <X size={12} />
                      <span>Remove</span>
                    </button>
                  </div>
                )}
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: 'var(--space-1)' }}
                disabled={uploadingVendorDoc || !selectedTender || !vendorFile}
              >
                {uploadingVendorDoc ? (
                  <>
                    <RefreshCw size={14} className="spinner" />
                    <span>Extracting PDF Text & Ingesting...</span>
                  </>
                ) : (
                  <>
                    <Upload size={14} />
                    <span>Upload & Extract Vendor Document</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Uploaded Vendor Documents Inventory Table */}
      <div className="gov-card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <FolderOpen size={16} style={{ color: 'var(--accent-primary)' }} />
              <span>Registered Vendor Bids for Active Tender</span>
            </div>
            <div className="card-subtitle">
              Verified document submissions scanned and ready for compliance matching
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onRefreshVendors}
          >
            <RefreshCw size={12} />
            <span>Refresh Submissions</span>
          </button>
        </div>

        {vendors && vendors.length > 0 ? (
          <div className="table-wrapper">
            <table className="gov-table">
              <thead>
                <tr>
                  <th style={{ width: '35%' }}>Vendor Legal Entity</th>
                  <th style={{ width: '15%' }}>Documents Uploaded</th>
                  <th style={{ width: '35%' }}>Files Registered</th>
                  <th style={{ width: '15%', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map((v) => (
                  <tr key={v.vendor_name}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {v.vendor_name}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Bidder ID: {v.vendor_name.slice(0, 16).replace(/[^a-zA-Z0-9]/g, '').toUpperCase()}
                      </div>
                    </td>
                    <td>
                      <span className="category-badge">
                        {v.document_count} {v.document_count === 1 ? 'file' : 'files'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {v.documents && v.documents.map((d) => (
                          <div
                            key={d.id}
                            style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <FileCheck size={12} style={{ color: 'var(--text-muted)' }} />
                            <span className="truncate" style={{ maxWidth: '320px' }}>
                              {d.filename}
                            </span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                              ({d.page_count} {d.page_count === 1 ? 'pg' : 'pgs'})
                            </span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={() => onNavigateToTab('compliance', v.vendor_name)}
                      >
                        <span>Evaluate & Report</span>
                        <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <FolderOpen size={36} className="empty-icon" />
            <div className="empty-title">No Vendor Documents Uploaded Yet</div>
            <div className="empty-desc">
              Upload bidder PDF submissions above to register vendors for compliance evaluation.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
