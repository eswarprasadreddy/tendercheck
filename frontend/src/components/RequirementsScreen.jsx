import React, { useState } from 'react';
import {
  FileText,
  Edit2,
  Trash2,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  BookOpen,
} from 'lucide-react';
import { api } from '../api';

export default function RequirementsScreen({
  selectedTender,
  requirements,
  loading,
  onRefreshRequirements,
  onNavigateToCompliance,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  // Edit Modal State
  const [editingReq, setEditingReq] = useState(null);
  const [editDesc, setEditDesc] = useState('');
  const [editCategory, setEditCategory] = useState('technical_spec');
  const [editType, setEditType] = useState('numeric');
  const [editOperator, setEditOperator] = useState('>=');
  const [editValueAmount, setEditValueAmount] = useState('');
  const [editUnit, setEditUnit] = useState('');
  const [editIsMandatory, setEditIsMandatory] = useState(true);
  const [savingEdit, setSavingEdit] = useState(false);
  const [editError, setEditError] = useState(null);

  // New Requirement Modal State
  const [isAddingReq, setIsAddingReq] = useState(false);
  const [newDesc, setNewDesc] = useState('');
  const [newCategory, setNewCategory] = useState('technical_spec');
  const [newType, setNewType] = useState('numeric');
  const [newOperator, setNewOperator] = useState('>=');
  const [newValueAmount, setNewValueAmount] = useState('');
  const [newUnit, setNewUnit] = useState('');
  const [newIsMandatory, setNewIsMandatory] = useState(true);
  const [savingNew, setSavingNew] = useState(false);
  const [newError, setNewError] = useState(null);

  // Delete State
  const [deletingId, setDeletingId] = useState(null);

  // Categories present in requirements
  const categories = ['ALL', ...new Set(requirements.map((r) => r.category))];

  // Filtering
  const filteredRequirements = requirements.filter((req) => {
    const matchesCategory =
      selectedCategory === 'ALL' || req.category === selectedCategory;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !query ||
      req.description.toLowerCase().includes(query) ||
      (req.source_quote && req.source_quote.toLowerCase().includes(query)) ||
      req.category.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });

  // Open Edit Modal
  const handleOpenEdit = (req) => {
    setEditingReq(req);
    setEditDesc(req.description);
    setEditCategory(req.category);
    setEditType(req.requirement_type);
    setEditOperator(req.operator || '>=');
    setEditValueAmount(
      req.value?.amount !== undefined ? String(req.value.amount) : req.value?.text_value || ''
    );
    setEditUnit(req.unit || req.value?.unit || '');
    setEditIsMandatory(req.is_mandatory);
    setEditError(null);
  };

  // Submit Edit
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editDesc.trim()) {
      setEditError('Description is required.');
      return;
    }
    setSavingEdit(true);
    setEditError(null);

    try {
      const payload = {
        description: editDesc.trim(),
        category: editCategory,
        requirement_type: editType,
        operator: editOperator,
        unit: editUnit || null,
        is_mandatory: editIsMandatory,
      };

      if (editType === 'numeric' || editType === 'spec') {
        const numVal = parseFloat(editValueAmount);
        if (!isNaN(numVal)) {
          payload.value = { amount: numVal, unit: editUnit };
        } else {
          payload.value = { text_value: editValueAmount };
        }
      } else if (editType === 'certification') {
        payload.value = { certificate_name: editDesc.trim(), required: true };
      }

      await api.updateRequirement(selectedTender.id, editingReq.id, payload);
      setEditingReq(null);
      await onRefreshRequirements();
    } catch (err) {
      setEditError(err.message || 'Failed to update requirement.');
    } finally {
      setSavingEdit(false);
    }
  };

  // Delete Requirement
  const handleDelete = async (reqId) => {
    if (!window.confirm('Are you sure you want to delete this requirement from the evaluation criteria?')) {
      return;
    }
    setDeletingId(reqId);
    try {
      await api.deleteRequirement(selectedTender.id, reqId);
      await onRefreshRequirements();
    } catch (err) {
      alert(`Error deleting requirement: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  // Create Requirement
  const handleSaveNew = async (e) => {
    e.preventDefault();
    if (!newDesc.trim()) {
      setNewError('Description is required.');
      return;
    }
    setSavingNew(true);
    setNewError(null);

    try {
      const payload = {
        description: newDesc.trim(),
        category: newCategory,
        requirement_type: newType,
        operator: newOperator,
        unit: newUnit || null,
        is_mandatory: newIsMandatory,
        source_page: 1,
        source_quote: 'Manually specified by Evaluation Officer',
      };

      if (newType === 'numeric' || newType === 'spec') {
        const numVal = parseFloat(newValueAmount);
        if (!isNaN(numVal)) {
          payload.value = { amount: numVal, unit: newUnit };
        } else {
          payload.value = { text_value: newValueAmount };
        }
      } else if (newType === 'certification') {
        payload.value = { certificate_name: newDesc.trim(), required: true };
      }

      await api.createRequirement(selectedTender.id, payload);
      setIsAddingReq(false);
      setNewDesc('');
      setNewValueAmount('');
      setNewUnit('');
      await onRefreshRequirements();
    } catch (err) {
      setNewError(err.message || 'Failed to create requirement.');
    } finally {
      setSavingNew(false);
    }
  };

  if (!selectedTender) {
    return (
      <div className="gov-card">
        <div className="empty-state">
          <BookOpen size={36} className="empty-icon" />
          <div className="empty-title">No Active Tender Selected</div>
          <div className="empty-desc">
            Please go to the "Tender & Vendor Upload" tab to upload or choose an active tender document first.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header Summary & Actions Bar */}
      <div className="gov-card" style={{ marginBottom: 'var(--space-2)' }}>
        <div className="card-header flex-between">
          <div>
            <div className="card-title">
              <FileText size={16} style={{ color: 'var(--accent-primary)' }} />
              <span>Extracted Tender Eligibility & Technical Criteria</span>
            </div>
            <div className="card-subtitle">
              {selectedTender.reference_number} | {requirements.length} total requirements parsed from tender document
            </div>
          </div>
          <div className="flex-gap-1">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onRefreshRequirements}
              disabled={loading}
            >
              <RefreshCw size={12} className={loading ? 'spinner' : ''} />
              <span>Refresh</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setIsAddingReq(true)}
            >
              <Plus size={14} />
              <span>Add Custom Requirement</span>
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onNavigateToCompliance}
            >
              <span>Proceed to Vendor Matching</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div
          style={{
            padding: 'var(--space-2) var(--space-3)',
            background: 'var(--bg-subtle)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-2)',
          }}
        >
          {/* Category Filter Chips */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: '4px' }}>
              Category:
            </span>
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`btn btn-sm ${selectedCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '2px 8px', fontSize: '11px' }}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div style={{ position: 'relative', width: '260px' }}>
            <Search
              size={14}
              style={{
                position: 'absolute',
                left: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
              }}
            />
            <input
              type="text"
              className="form-input"
              placeholder="Search criteria, quotes..."
              style={{ paddingLeft: '28px', paddingRight: '8px', height: '30px', fontSize: '12px' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Requirements Table */}
      <div className="gov-card">
        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            <div style={{ fontSize: '13px' }}>Loading extracted requirements...</div>
          </div>
        ) : filteredRequirements.length > 0 ? (
          <div className="table-wrapper">
            <table className="gov-table">
              <thead>
                <tr>
                  <th style={{ width: '4%' }}>#</th>
                  <th style={{ width: '13%' }}>Category</th>
                  <th style={{ width: '38%' }}>Requirement Specification</th>
                  <th style={{ width: '15%' }}>Benchmark Rule</th>
                  <th style={{ width: '18%' }}>Tender Source / Page</th>
                  <th style={{ width: '12%', textAlign: 'right' }}>Officer Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequirements.map((req, idx) => (
                  <tr key={req.id}>
                    <td style={{ color: 'var(--text-muted)', fontWeight: 500 }}>
                      {idx + 1}
                    </td>
                    <td>
                      <span className="category-badge">
                        {req.category.replace('_', ' ')}
                      </span>
                      {req.is_mandatory && (
                        <div style={{ fontSize: '10px', color: 'var(--status-fail-text)', fontWeight: 600, marginTop: '2px' }}>
                          MANDATORY
                        </div>
                      )}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                        {req.description}
                      </div>
                      {req.sector_key && (
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                          key: {req.sector_key}
                        </div>
                      )}
                    </td>
                    <td>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {req.operator ? `${req.operator} ` : ''}
                        {req.value?.amount !== undefined ? (
                          <span>
                            {req.value.amount.toLocaleString()} {req.unit || req.value.unit || ''}
                          </span>
                        ) : req.value?.text_value ? (
                          <span>{req.value.text_value}</span>
                        ) : req.value?.certificate_name ? (
                          <span>{req.value.certificate_name}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>Verified Document Required</span>
                        )}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Type: {req.requirement_type}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        <strong>Page {req.source_page}</strong>
                      </div>
                      <div
                        className="truncate"
                        style={{
                          fontSize: '11px',
                          color: 'var(--text-muted)',
                          fontStyle: 'italic',
                          maxWidth: '220px',
                        }}
                        title={req.source_quote}
                      >
                        &ldquo;{req.source_quote}&rdquo;
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '4px' }}>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '3px 6px' }}
                          title="Edit requirement criteria"
                          onClick={() => handleOpenEdit(req)}
                        >
                          <Edit2 size={12} />
                          <span>Edit</span>
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          style={{ padding: '3px 6px' }}
                          title="Delete invalid requirement"
                          disabled={deletingId === req.id}
                          onClick={() => handleDelete(req.id)}
                        >
                          <Trash2 size={12} />
                          <span>Del</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <FileText size={36} className="empty-icon" />
            <div className="empty-title">No Matching Requirements Found</div>
            <div className="empty-desc">
              {searchQuery || selectedCategory !== 'ALL'
                ? 'No criteria match your filter. Try selecting "ALL" or clearing the search box.'
                : 'No requirements have been registered for this tender yet.'}
            </div>
          </div>
        )}
      </div>

      {/* Edit Requirement Modal Dialog */}
      {editingReq && (
        <>
          <div className="modal-backdrop" onClick={() => setEditingReq(null)} />
          <div className="modal-dialog">
            <div className="modal-header">
              <div style={{ fontWeight: 600, fontSize: '15px' }}>
                Officer Edit: Tender Requirement
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setEditingReq(null)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleSaveEdit}>
              <div className="modal-body">
                {editError && (
                  <div className="status-badge fail" style={{ width: '100%', marginBottom: 'var(--space-2)' }}>
                    <AlertCircle size={14} />
                    <span>{editError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label" htmlFor="edit-desc">
                    Requirement Description *
                  </label>
                  <textarea
                    id="edit-desc"
                    className="form-textarea"
                    rows={3}
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-category">
                      Category
                    </label>
                    <select
                      id="edit-category"
                      className="form-select"
                      value={editCategory}
                      onChange={(e) => setEditCategory(e.target.value)}
                    >
                      <option value="technical_spec">Technical Specification</option>
                      <option value="financial">Financial (Turnover, Net Worth)</option>
                      <option value="experience">Experience & Past Orders</option>
                      <option value="certification">Certification (ISO, BIS)</option>
                      <option value="delivery">Delivery & Warranty</option>
                      <option value="legal">Legal & Statutory (GST)</option>
                      <option value="compliance">Local Compliance (MII)</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-type">
                      Verification Checker
                    </label>
                    <select
                      id="edit-type"
                      className="form-select"
                      value={editType}
                      onChange={(e) => setEditType(e.target.value)}
                    >
                      <option value="numeric">Numeric Engine (&gt;=, &le;)</option>
                      <option value="spec">Hardware Spec Engine</option>
                      <option value="certification">Certification Existence</option>
                      <option value="boolean">Boolean Document Check</option>
                      <option value="text">Text / Model Match</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-2)' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-operator">
                      Operator
                    </label>
                    <select
                      id="edit-operator"
                      className="form-select"
                      value={editOperator}
                      onChange={(e) => setEditOperator(e.target.value)}
                    >
                      <option value=">=">&gt;= (At least)</option>
                      <option value="==">== (Exact)</option>
                      <option value="<=">&lt;= (At most)</option>
                      <option value="exists">Exists</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-amount">
                      Threshold / Value
                    </label>
                    <input
                      id="edit-amount"
                      type="text"
                      className="form-input"
                      value={editValueAmount}
                      onChange={(e) => setEditValueAmount(e.target.value)}
                      placeholder="e.g. 16 or 20000000"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-unit">
                      Unit
                    </label>
                    <input
                      id="edit-unit"
                      type="text"
                      className="form-input"
                      value={editUnit}
                      onChange={(e) => setEditUnit(e.target.value)}
                      placeholder="e.g. GB, INR, years"
                    />
                  </div>
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 'var(--space-1)' }}>
                  <input
                    id="edit-mandatory"
                    type="checkbox"
                    checked={editIsMandatory}
                    onChange={(e) => setEditIsMandatory(e.target.checked)}
                  />
                  <label htmlFor="edit-mandatory" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}>
                    Mandatory Qualification Condition (Failure disqualifies bidder)
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setEditingReq(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={savingEdit}
                >
                  {savingEdit ? 'Updating...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </>
      )}

      {/* Add Custom Requirement Modal Dialog */}
      {isAddingReq && (
        <>
          <div className="modal-backdrop" onClick={() => setIsAddingReq(false)} />
          <div className="modal-dialog">
            <div className="modal-header">
              <div style={{ fontWeight: 600, fontSize: '15px' }}>
                Officer: Add Custom Tender Requirement
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsAddingReq(false)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleSaveNew}>
              <div className="modal-body">
                {newError && (
                  <div className="status-badge fail" style={{ width: '100%', marginBottom: 'var(--space-2)' }}>
                    <AlertCircle size={14} />
                    <span>{newError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label" htmlFor="new-desc">
                    Requirement Description *
                  </label>
                  <textarea
                    id="new-desc"
                    className="form-textarea"
                    rows={3}
                    placeholder="e.g. OEM Authorization: Bidder must furnish Manufacturer Authorization Form (MAF)"
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="new-cat">
                      Category
                    </label>
                    <select
                      id="new-cat"
                      className="form-select"
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                    >
                      <option value="technical_spec">Technical Specification</option>
                      <option value="financial">Financial (Turnover, Net Worth)</option>
                      <option value="experience">Experience & Past Orders</option>
                      <option value="certification">Certification (ISO, BIS)</option>
                      <option value="delivery">Delivery & Warranty</option>
                      <option value="legal">Legal & Statutory (GST)</option>
                      <option value="compliance">Local Compliance (MII)</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="new-type">
                      Verification Checker
                    </label>
                    <select
                      id="new-type"
                      className="form-select"
                      value={newType}
                      onChange={(e) => setNewType(e.target.value)}
                    >
                      <option value="numeric">Numeric Engine (&gt;=, &le;)</option>
                      <option value="spec">Hardware Spec Engine</option>
                      <option value="certification">Certification Existence</option>
                      <option value="boolean">Boolean Document Check</option>
                      <option value="text">Text / Model Match</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-2)' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="new-op">
                      Operator
                    </label>
                    <select
                      id="new-op"
                      className="form-select"
                      value={newOperator}
                      onChange={(e) => setNewOperator(e.target.value)}
                    >
                      <option value=">=">&gt;= (At least)</option>
                      <option value="==">== (Exact)</option>
                      <option value="<=">&lt;= (At most)</option>
                      <option value="exists">Exists</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="new-amount">
                      Threshold / Value
                    </label>
                    <input
                      id="new-amount"
                      type="text"
                      className="form-input"
                      value={newValueAmount}
                      onChange={(e) => setNewValueAmount(e.target.value)}
                      placeholder="e.g. 16 or 5000000"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="new-unit">
                      Unit
                    </label>
                    <input
                      id="new-unit"
                      type="text"
                      className="form-input"
                      value={newUnit}
                      onChange={(e) => setNewUnit(e.target.value)}
                      placeholder="e.g. GB, INR, years"
                    />
                  </div>
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 'var(--space-1)' }}>
                  <input
                    id="new-mandatory"
                    type="checkbox"
                    checked={newIsMandatory}
                    onChange={(e) => setNewIsMandatory(e.target.checked)}
                  />
                  <label htmlFor="new-mandatory" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}>
                    Mandatory Qualification Condition (Failure disqualifies bidder)
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsAddingReq(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={savingNew}
                >
                  {savingNew ? 'Adding...' : 'Add Requirement'}
                </button>
              </div>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
