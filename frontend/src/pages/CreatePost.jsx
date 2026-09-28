import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api.js'

export default function CreatePost({ user }) {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [details, setDetails] = useState('')
  const [video, setVideo] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!user) return <Navigate to="/login" replace />

  async function submit(event) {
    event.preventDefault()
    if (!video) {
      setError('Choose a video first.')
      return
    }

    setBusy(true)
    setError('')
    const body = new FormData()
    body.append('title', title)
    body.append('details', details)
    body.append('video', video)

    try {
      await api('/me/posts', { method: 'POST', body })
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page auth-page">
      <form className="form-card wide-form" onSubmit={submit}>
        <h1>Post a city issue</h1>
        <p className="muted">Your location will be shown as {user.city}, {user.country}.</p>
        {error && <div className="form-error">{error}</div>}

        <label>
          Title
          <input maxLength="80" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Details
          <textarea maxLength="2000" rows="6" value={details} onChange={(e) => setDetails(e.target.value)} required />
        </label>
        <label>
          Video
          <input type="file" accept="video/mp4,video/webm,video/quicktime,video/x-matroska" onChange={(e) => setVideo(e.target.files?.[0] || null)} required />
          <span className="field-note">MP4 or WebM is best for browser playback. Maximum size is controlled by the backend.</span>
        </label>

        <button className="primary-button full" disabled={busy}>
          {busy ? 'Uploading…' : 'Publish video'}
        </button>
      </form>
    </main>
  )
}
