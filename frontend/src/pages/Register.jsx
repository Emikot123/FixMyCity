import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api.js'

export default function Register({ user }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    country: '',
    city: '',
    age: '',
  })
  const [picture, setPicture] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  function change(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    const body = new FormData()
    Object.entries(form).forEach(([key, value]) => body.append(key, value))
    if (picture) body.append('profile_picture', picture)

    try {
      await api('/auth/register', { method: 'POST', body })
      navigate(`/verify?mode=signup&email=${encodeURIComponent(form.email.trim().toLowerCase())}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page auth-page">
      <form className="form-card wide-form" onSubmit={submit}>
        <h1>Create account</h1>
        <p className="muted">Create your FixMyCity profile and verify it by email.</p>
        {error && <div className="form-error">{error}</div>}

        <div className="form-grid">
          <label>
            Username
            <input name="username" minLength="3" maxLength="30" value={form.username} onChange={change} required />
          </label>
          <label>
            Email
            <input name="email" type="email" value={form.email} onChange={change} required />
          </label>
          <label>
            Password
            <input name="password" type="password" minLength="6" maxLength="72" value={form.password} onChange={change} required />
          </label>
          <label>
            Age
            <input name="age" type="number" min="13" max="120" value={form.age} onChange={change} required />
          </label>
          <label>
            Country
            <input name="country" value={form.country} onChange={change} required />
          </label>
          <label>
            City
            <input name="city" value={form.city} onChange={change} required />
          </label>
        </div>

        <label>
          Profile picture <span className="muted">(optional)</span>
          <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setPicture(e.target.files?.[0] || null)} />
        </label>

        <button className="primary-button full" disabled={busy}>
          {busy ? 'Sending code…' : 'Create account'}
        </button>
        <p className="form-foot">Already registered? <Link to="/login">Log in</Link></p>
      </form>
    </main>
  )
}
