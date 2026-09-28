import { useState } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'

export default function Verify({ setUser }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const email = params.get('email') || ''
  const mode = params.get('mode')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!email || !['signup', 'login'].includes(mode)) {
    return <Navigate to="/login" replace />
  }

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    const body = new FormData()
    body.append('email', email)
    body.append('code', code)

    try {
      const user = await api(mode === 'signup' ? '/auth/verify_signup' : '/auth/verify_login', {
        method: 'POST',
        body,
      })
      setUser(user)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page auth-page">
      <form className="form-card" onSubmit={submit}>
        <h1>Verify email</h1>
        <p className="muted">Enter the 6-digit code sent to <strong>{email}</strong>.</p>
        {error && <div className="form-error">{error}</div>}
        <label>
          Verification code
          <input
            className="code-input"
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength="6"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            required
            autoFocus
          />
        </label>
        <button className="primary-button full" disabled={busy || code.length !== 6}>
          {busy ? 'Verifying…' : 'Verify'}
        </button>
      </form>
    </main>
  )
}
