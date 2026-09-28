import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api.js'

export default function Login({ user }) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    const form = new FormData()
    form.append('email', email)
    form.append('password', password)

    try {
      await api('/auth/login', { method: 'POST', body: form })
      navigate(`/verify?mode=login&email=${encodeURIComponent(email.trim().toLowerCase())}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page auth-page">
      <form className="form-card" onSubmit={submit}>
        <h1>Log in</h1>
        <p className="muted">Enter your account details. We’ll send a verification code to your email.</p>
        {error && <div className="form-error">{error}</div>}

        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>

        <button className="primary-button full" disabled={busy}>
          {busy ? 'Sending code…' : 'Continue'}
        </button>
        <p className="form-foot">No account? <Link to="/register">Sign up</Link></p>
      </form>
    </main>
  )
}
