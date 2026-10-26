// TenderCheck API Client

const BASE_URL = '';

async function request(url, options = {}) {
  const res = await fetch(`${BASE_URL}${url}`, options);
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // ignore json parse error
    }
    const err = new Error(errorDetail);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) {
    return null;
  }
  return res.json();
}

export const api = {
  // Tenders
  getTenders: () => request('/api/v1/tenders'),
  getTender: (id) => request(`/api/v1/tenders/${id}`),
  uploadTender: (formData) =>
    request('/api/v1/tenders/upload', {
      method: 'POST',
      body: formData,
    }),

  // Requirements
  getRequirements: (tenderId) => request(`/api/v1/tenders/${tenderId}/requirements`),
  updateRequirement: (tenderId, reqId, payload) =>
    request(`/api/v1/tenders/${tenderId}/requirements/${reqId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  deleteRequirement: (tenderId, reqId) =>
    request(`/api/v1/tenders/${tenderId}/requirements/${reqId}`, {
      method: 'DELETE',
    }),
  createRequirement: (tenderId, payload) =>
    request(`/api/v1/tenders/${tenderId}/requirements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // Vendors & Documents
  getVendors: (tenderId) => request(`/api/v1/tenders/${tenderId}/vendors`),
  uploadVendorDocument: (tenderId, formData) =>
    request(`/api/v1/tenders/${tenderId}/vendors/upload`, {
      method: 'POST',
      body: formData,
    }),
  getVendorDocuments: (tenderId, vendorName) =>
    request(`/api/v1/tenders/${tenderId}/vendors/${encodeURIComponent(vendorName)}/documents`),

  // Matching & Reports
  runMatching: (tenderId, vendorName) =>
    request(`/api/v1/tenders/${tenderId}/vendors/${encodeURIComponent(vendorName)}/match`, {
      method: 'POST',
    }),
  getVendorReport: (tenderId, vendorName) =>
    request(`/api/v1/tenders/${tenderId}/vendors/${encodeURIComponent(vendorName)}/report`),
  generateVendorReport: (tenderId, vendorName) =>
    request(`/api/v1/tenders/${tenderId}/vendors/${encodeURIComponent(vendorName)}/report`, {
      method: 'POST',
    }),
  getContradictions: (tenderId, vendorName) =>
    request(`/api/v1/tenders/${tenderId}/vendors/${encodeURIComponent(vendorName)}/contradictions`),

  // Officer Match Override
  updateMatchVerdict: (matchId, payload) =>
    request(`/api/v1/matches/${matchId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // Officer Final Sign-Off
  confirmReport: (payload) =>
    request('/report/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
};
