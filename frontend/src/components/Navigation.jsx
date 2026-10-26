import React from 'react';
import { UploadCloud, FileText, CheckSquare } from 'lucide-react';

export default function Navigation({ activeTab, onSelectTab, counts }) {
  return (
    <nav className="tab-navigation">
      <button
        type="button"
        className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
        onClick={() => onSelectTab('upload')}
      >
        <UploadCloud size={16} />
        <span>1. Tender & Vendor Upload</span>
        {counts?.documents !== undefined && (
          <span className="nav-badge-count">{counts.documents}</span>
        )}
      </button>

      <button
        type="button"
        className={`nav-tab ${activeTab === 'requirements' ? 'active' : ''}`}
        onClick={() => onSelectTab('requirements')}
      >
        <FileText size={16} />
        <span>2. Extracted Requirements</span>
        {counts?.requirements !== undefined && (
          <span className="nav-badge-count">{counts.requirements}</span>
        )}
      </button>

      <button
        type="button"
        className={`nav-tab ${activeTab === 'compliance' ? 'active' : ''}`}
        onClick={() => onSelectTab('compliance')}
      >
        <CheckSquare size={16} />
        <span>3. Compliance Report & Officer Review</span>
        {counts?.matches !== undefined && (
          <span className="nav-badge-count">{counts.matches}</span>
        )}
      </button>
    </nav>
  );
}
