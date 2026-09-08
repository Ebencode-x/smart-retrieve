const API_BASE = "https://smart-temporary-exam-entry-var.onrender.com";

const API = {
  getToken() { return localStorage.getItem("access_token"); },
  setToken(t) { localStorage.setItem("access_token", t); },
  getRole() { return localStorage.getItem("role"); },
  setRole(r) { localStorage.setItem("role", r); },
  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("role");
    window.location.href = "/";
  },
  requireAuth() {
    if (!this.getToken()) window.location.href = "/";
  },
  requireRole(allowedRoles) {
    this.requireAuth();
    if (!allowedRoles.includes(this.getRole())) {
      window.location.href = "/dashboard";
      return false;
    }
    return true;
  },
  async request(path, options = {}) {
    const headers = options.headers || {};
    headers["Content-Type"] = "application/json";
    const token = this.getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    const res = await fetch(API_BASE + path, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  },
  // For endpoints that return a file (PDF / xlsx) rather than JSON.
  // Downloads it straight to the browser using the auth token.
  async download(path, fallbackFilename) {
    const token = this.getToken();
    const res = await fetch(API_BASE + path, {
      headers: token ? { "Authorization": "Bearer " + token } : {}
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw { status: res.status, data };
    }
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename=([^;]+)/);
    const filename = match ? match[1].trim() : fallbackFilename;
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }
};

const ROLE_LABELS = {
  student: "Student",
  gate_security: "Gate Security",
  invigilator: "Invigilator",
  exams_officer: "Exams Officer",
  admin: "Administrator",
  security: "Security (legacy)"
};

function roleLabel(role) {
  return ROLE_LABELS[role] || role;
}

function decodeJWT(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch (e) {
    return null;
  }
}
