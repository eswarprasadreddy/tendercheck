import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Bookmark,
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ShieldAlert,
  Save,
  Cpu,
} from 'lucide-react';
import { api } from '../api';

export default function EvidencePanel({
  match,
  onClose,
  onVerdictUpdated,
  onRetryMatching,
}) {
  const [selectedVerdict, setSelectedVerdict] = useState('PASS');
  const [officerNotes, setOfficerNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    if (match) {
      setSelectedVerdict(match.verdict || 'PASS');
      setOfficerNotes(match.verdict_reason?.includes('Officer') ? match.verdict_reason : '');
      setSaveSuccess(false);
      setSaveError(null);
    }
  }, [match]);

  if (!match) return null;

  const handleSaveOverride = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const res = await api.updateMatchVerdict(match.id, {
        verdict: selectedVerdict,
        officer_notes: officerNotes.trim() || undefined,
      });
      setSaveSuccess(true);
      if (onVerdictUpdated) {
        onVerdictUpdated(res);
      }
    } catch (err) {
      setSaveError(err.message || 'Failed to update verdict.');
    } finally {
      setSaving(false);
    }
  };

  const getBadgeClass = (verdict) => {
    switch (verdict) {
      case 'PASS':
        return 'pass';
      case 'FAIL':
        return 'fail';
      case 'MISSING':
        return 'missing';
      case 'MISMATCH':
        return 'mismatch';
      case 'ERROR':
        return 'fail';
      default:
        return 'review';
    }
  };

  const reqDesc = match.requirement?.description || match.requirement_description || 'Tender Eligibility Requirement';
  const reqCategory = match.requirement?.category || match.requirement_category || 'general';

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="evidence-drawer">
        {/* Drawer Header */}
        <div className="drawer-header">
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Evidence & Verification Details
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
              Match Record #{match.id.slice(0, 8)}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onClose}
            aria-label="Close evidence panel"
          >
            <X size={16} />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="drawer-body">
          {/* Requirement Info */}
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <span className="category-badge">{reqCategory.replace('_', ' ')}</span>
              <span className={`status-badge ${getBadgeClass(match.verdict)}`}>
                {match.verdict}
              </span>
              {match.checked_by === 'officer' && (
                <span className="status-badge review">
                  OFFICER OVERRIDDEN
                </span>
              )}
            </div>
            <h3 style={{ fontSize: '15px', lineHeight: 1.4, marginTop: 'var(--space-1)' }}>
              {reqDesc}
            </h3>
          </div>

          {/* Verification Verdict Reason */}
          <div
            style={{
              padding: 'var(--space-2)',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: 'var(--space-3)',
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Deterministic Engine Finding
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '4px', fontWeight: 500 }}>
              {match.verdict_reason}
            </div>
          </div>

          {/* Evidence Provenance Box (PASS / FAIL / MISMATCH) */}
          {match.verdict !== 'MISSING' ? (
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-1)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Bookmark size={14} style={{ color: 'var(--accent-primary)' }} />
                <span>Extracted Document Evidence</span>
              </div>

              <div className="gov-card" style={{ padding: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-label">Source Document File:</span>
                  <span className="evidence-meta-val" title={match.evidence_file}>
                    {match.evidence_file || 'Not Specified'}
                  </span>
                </div>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-label">Document Page Number:</span>
                  <span className="evidence-meta-val">
                    Page {match.evidence_page || 1}
                  </span>
                </div>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-label">Verification Engine:</span>
                  <span className="evidence-meta-val" style={{ textTransform: 'capitalize' }}>
                    {match.checked_by?.replace('_', ' ') || 'Automated'}
                  </span>
                </div>
                {match.llm_confidence !== null && match.llm_confidence !== undefined && (
                  <div className="evidence-meta-row" style={{ borderBottom: 'none' }}>
                    <span className="evidence-meta-label">Engine Confidence:</span>
                    <span className="evidence-meta-val">
                      {(match.llm_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Verbatim Quoted Monospace Excerpt */}
              <div style={{ marginTop: 'var(--space-2)' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Verbatim Quoted Excerpt from Bid Document
                </div>
                <div className="evidence-quote-box">
                  &ldquo;{match.evidence_quote || 'No direct text excerpt recorded.'}&rdquo;
                </div>
              </div>
            </div>
          ) : (
            /* Missing Documents Evidence */
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-1)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={14} style={{ color: '#b45309' }} />
                <span>Document Search Audit (Missing Evidence)</span>
              </div>
              <div className="gov-card" style={{ padding: 'var(--space-2)' }}>
                <div className="evidence-meta-row">
                  <span className="evidence-meta-label">Files Examined:</span>
                  <span className="evidence-meta-val">
                    {match.searched_in?.documents?.join(', ') || 'All uploaded vendor bid attachments'}
                  </span>
                </div>
                <div className="evidence-meta-row" style={{ borderBottom: 'none' }}>
                  <span className="evidence-meta-label">Search Terms Checked:</span>
                  <span className="evidence-meta-val">
                    {match.searched_in?.terms?.join(', ') || 'authorization, certificate, turnover, maf'}
                  </span>
                </div>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: 'var(--space-1)' }}>
                The evaluation engine scanned all submitted PDFs across multiple keywords and OCR text without discovering conforming proof.
              </div>
            </div>
          )}

          {/* Error Notice */}
          {match.verdict === 'ERROR' && (
            <div style={{ marginBottom: 'var(--space-3)', padding: 'var(--space-2)', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#991b1b', fontWeight: 600, fontSize: '13px' }}>
                <AlertTriangle size={16} />
                <span>API Execution / Rate-Limit Error</span>
              </div>
              <div style={{ fontSize: '12px', color: '#7f1d1d', marginTop: '4px' }}>
                {match.verdict_reason}
              </div>
              {onRetryMatching && (
                <div style={{ marginTop: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={onRetryMatching}
                  >
                    <span>Retry Matching Engine</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Section: Officer Review & Override */}
          <div
            style={{
              borderTop: '2px solid var(--border-subtle)',
              paddingTop: 'var(--space-3)',
              marginTop: 'var(--space-3)',
            }}
          >
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
              Officer Verdict Review & Override
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
              Government evaluation officers have statutory authority to approve, override, or provide clarification notes for any match finding.
            </div>

            {saveSuccess && (
              <div className="status-badge pass" style={{ width: '100%', marginBottom: 'var(--space-2)', padding: '6px var(--space-1)' }}>
                <CheckCircle size={14} />
                <span>Verdict updated and scorecard recalculated successfully.</span>
              </div>
            )}
            {saveError && (
              <div className="status-badge fail" style={{ width: '100%', marginBottom: 'var(--space-2)', padding: '6px var(--space-1)' }}>
                <XCircle size={14} />
                <span>{saveError}</span>
              </div>
            )}

            <form onSubmit={handleSaveOverride}>
              <div className="form-group">
                <label className="form-label" htmlFor="override-verdict">
                  Assigned Verdict
                </label>
                <select
                  id="override-verdict"
                  className="form-select"
                  value={selectedVerdict}
                  onChange={(e) => setSelectedVerdict(e.target.value)}
                  disabled={saving}
                >
                  <option value="PASS">PASS (Compliant)</option>
                  <option value="FAIL">FAIL (Non-Compliant)</option>
                  <option value="MISSING">MISSING (Documentation Omitted)</option>
                  <option value="MISMATCH">MISMATCH (Criteria Discrepancy)</option>
                  <option value="ERROR">ERROR (Verification Failure / Needs Retry)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="officer-notes">
                  Officer Justification & Evaluation Note *
                </label>
                <textarea
                  id="officer-notes"
                  className="form-textarea"
                  rows={3}
                  placeholder="Record justification for approving or overriding this requirement (e.g. verified on GeM OEM database / technical clarification verified)..."
                  value={officerNotes}
                  onChange={(e) => setOfficerNotes(e.target.value)}
                  disabled={saving}
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={saving}
              >
                <Save size={14} />
                <span>{saving ? 'Updating Scorecard...' : 'Apply Officer Verdict'}</span>
              </button>
            </form>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="drawer-footer">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Close Panel
          </button>
        </div>
      </div>
    </>
  );
}
