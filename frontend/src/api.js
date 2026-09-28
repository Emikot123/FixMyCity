export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export async function api(path, options = {}) {
  const requestOptions = {
    credentials: 'include',
    ...options,
    headers: {
      ...(options.headers || {}),
    },
  }

  if (options.body && !(options.body instanceof FormData) && typeof options.body !== 'string') {
    requestOptions.headers['Content-Type'] = 'application/json'
    requestOptions.body = JSON.stringify(options.body)
  }

  const response = await fetch(`${API_URL}${path}`, requestOptions)

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    let message = 'Request failed'
    if (typeof data === 'object' && data?.detail) {
      message = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg || 'Invalid value').join(', ')
        : data.detail
    } else if (typeof data === 'string' && data) {
      message = data
    }
    throw new Error(message)
  }

  return data
}

export function mediaUrl(path) {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  return `${API_URL}${path}`
}
