import React from 'react';
import { ShieldCheck, Plus } from 'lucide-react';

export default function Header({
  tenders,
  selectedTender,
  onSelectTender,
  officerId,
  onLogout,
}) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-emblem" title="Government Tender Verification">
          TC
        </div>
        <div>
          <div className="brand-title">
            TenderCheck
            <span className="brand-tag">GovTech Portal</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.02em' }}>
            DIRECTORATE OF PUBLIC PROCUREMENT | COMPLIANCE VERIFICATION
          </div>
        </div>
      </div>

      <div className="header-right">
        <div className="flex-gap-1" style={{ alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onSelectTender(null)}
            style={{
              fontSize: '11px',
              padding: '4px 10px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
            }}
            title="Clear active selection to upload a new tender"
          >
            <Plus size={12} />
            <span>New Tender</span>
          </button>

          {tenders && tenders.length > 0 && (
            <>
              <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>
                Active Tender:
              </span>
              <select
                className="form-select"
                style={{ width: '280px', padding: '4px 8px', fontSize: '12px' }}
                value={selectedTender ? selectedTender.id : ''}
                onChange={(e) => {
                  const val = e.target.value;
                  if (!val) {
                    onSelectTender(null);
                  } else {
                    const found = tenders.find((t) => t.id === val);
                    if (found) onSelectTender(found);
                  }
                }}
              >
                <option value="">-- No Active Tender (Start New) --</option>
                {tenders.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.reference_number} - {t.title.slice(0, 36)}...
                  </option>
                ))}
              </select>
            </>
          )}
        </div>

        <div className="officer-badge" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={14} style={{ color: 'var(--accent-primary)' }} />
          <span>Signed in as: <strong>{officerId || 'OFFICER-7821'}</strong></span>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              style={{
                marginLeft: '8px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '11px',
                textDecoration: 'underline',
                padding: '2px 4px',
              }}
              title="Sign out of GovTech Portal"
            >
              Sign out
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
