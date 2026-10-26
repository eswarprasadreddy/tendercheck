import React, { useState } from 'react';
import { Shield, AlertCircle, ArrowRight } from 'lucide-react';

export default function LoginScreen({ onLogin }) {
  // Empty input fields by default as requested
  const [username, setUsername] = useState('');
  const [officerId, setOfficerId] = useState('');
  const [department, setDepartment] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please provide Officer Identity and Passcode.');
      return;
    }

    setLoading(true);
    setError('');

    setTimeout(() => {
      setLoading(false);
      onLogin({
        username: username.trim(),
        officerId: officerId.trim() || 'OFFICER-7821',
        department: department.trim() || 'Directorate of Public Procurement',
      });
    }, 300);
  };

  const handleApplyPreset = (badgeId, user, dept) => {
    setUsername(user);
    setOfficerId(badgeId);
    setDepartment(dept);
    setPassword('GovPass#2026');
    setError('');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-app)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 'var(--space-3)',
        fontFamily: 'var(--font-family)',
      }}
    >
      <div
        className="gov-card"
        style={{
          width: '100%',
          maxWidth: '440px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)',
          border: '1px solid var(--border-default)',
        }}
      >
        {/* Institutional Card Header */}
        <div
          style={{
            padding: 'var(--space-3)',
            borderBottom: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <div className="header-emblem" style={{ width: '36px', height: '36px', fontSize: '15px' }}>
              TC
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                <h1 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>TenderCheck</h1>
                <span className="brand-tag">GovTech</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '2px' }}>
                Directorate of Public Procurement | GFR 2017
              </div>
            </div>
          </div>
        </div>

        {/* Authentication Form Body */}
        <div style={{ padding: 'var(--space-3)' }}>
          <div style={{ marginBottom: 'var(--space-2)' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Officer Authentication
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
              Enter government clearance credentials to inspect and verify procurement bids.
            </p>
          </div>

          {error && (
            <div
              className="status-badge fail"
              style={{
                width: '100%',
                padding: 'var(--space-1) var(--space-2)',
                marginBottom: 'var(--space-2)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="officer-user">
                Officer Identity / Username *
              </label>
              <input
                id="officer-user"
                type="text"
                className="form-input"
                placeholder="e.g. officer.sharma"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="off"
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="officer-id">
                Officer ID Badge
              </label>
              <input
                id="officer-id"
                type="text"
                className="form-input"
                placeholder="e.g. OFFICER-7821"
                value={officerId}
                onChange={(e) => setOfficerId(e.target.value)}
                autoComplete="off"
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="officer-dept">
                Department / Ministry
              </label>
              <input
                id="officer-dept"
                type="text"
                className="form-input"
                placeholder="e.g. Ministry of Electronics & IT"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                autoComplete="off"
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="officer-pass">
                Security Passcode *
              </label>
              <input
                id="officer-pass"
                type="password"
                className="form-input"
                placeholder="Enter passcode"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{
                width: '100%',
                marginTop: 'var(--space-1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 'var(--space-1)',
                padding: 'var(--space-1) var(--space-2)',
              }}
            >
              {loading ? (
                <span>Authenticating Officer...</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </form>

          {/* Quick Select Preset Profiles */}
          <div
            style={{
              marginTop: 'var(--space-3)',
              paddingTop: 'var(--space-2)',
              borderTop: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 'var(--space-1)', fontWeight: 600, textTransform: 'uppercase' }}>
              Testing Profiles (Click to Populate):
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() =>
                  handleApplyPreset(
                    'OFFICER-7821',
                    'officer.sharma',
                    'Ministry of Electronics & IT'
                  )
                }
                style={{
                  justifyContent: 'space-between',
                  width: '100%',
                  fontWeight: 400,
                  fontSize: '12px',
                }}
              >
                <span><strong>OFFICER-7821</strong> - MeitY Procurement</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Select</span>
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() =>
                  handleApplyPreset(
                    'AUDITOR-4019',
                    'auditor.verma',
                    'Comptroller & Auditor General'
                  )
                }
                style={{
                  justifyContent: 'space-between',
                  width: '100%',
                  fontWeight: 400,
                  fontSize: '12px',
                }}
              >
                <span><strong>AUDITOR-4019</strong> - Statutory Auditor</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Select</span>
              </button>
            </div>
          </div>
        </div>

        {/* Security Footer */}
        <div
          style={{
            padding: 'var(--space-1) var(--space-3)',
            backgroundColor: 'var(--bg-subtle)',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>TLS 1.3 Certified</span>
          <span>Central Public Procurement Portal</span>
        </div>
      </div>
    </div>
  );
}
