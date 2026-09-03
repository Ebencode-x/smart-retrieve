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
  async request(path, options = {}) {
    const headers = options.headers || {};
    headers["Content-Type"] = "application/json";
    const token = this.getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    const res = await fetch(API_BASE + path, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  }
};

function decodeJWT(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch (e) {
    return null;
  }
}
