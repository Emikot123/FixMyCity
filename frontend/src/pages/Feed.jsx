import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import VideoCard from '../components/VideoCard.jsx'

export default function Feed({ user }) {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/posts')
      .then(setPosts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <main className="page feed-page">
      <section className="page-heading compact-heading">
        <div>
          <h1>Community feed</h1>
          <p>See city issues reported by people nearby.</p>
        </div>
        {user && <Link className="primary-button" to="/post">Post a video</Link>}
      </section>

      {loading && <div className="status-card">Loading posts…</div>}
      {error && <div className="error-card">{error}</div>}
      {!loading && !error && posts.length === 0 && (
        <div className="empty-card">
          <h2>No reports yet</h2>
          <p>Be the first person to post a city issue.</p>
          {user ? <Link to="/post">Create the first post</Link> : <Link to="/login">Log in to post</Link>}
        </div>
      )}

      <div className="feed-list">
        {posts.map((post) => (
          <VideoCard key={post.id} post={post} currentUser={user} />
        ))}
      </div>
    </main>
  )
}
