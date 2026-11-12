const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const description = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body);
    throw new Error(`HTTP ${response.status}: ${description}`);
  }
  return body;
}

export const post = (path, data) => request(path, {method: 'POST', body: JSON.stringify(data)});
