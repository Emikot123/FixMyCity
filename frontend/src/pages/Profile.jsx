import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api.js'
import Avatar from '../components/Avatar.jsx'
import VideoCard from '../components/VideoCard.jsx'

export default function Profile({ user }) {
  const [posts, setPosts] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) return
    api('/me/posts').then(setPosts).catch((err) => setError(err.message))
  }, [user])

  if (!user) return <Navigate to="/login" replace />

  function removeFromList(id) {
    setPosts((current) => current.filter((post) => post.id !== id))
  }

  return (
    <main className="page profile-page">
      <section className="profile-header">
        <Avatar user={user} size={74} />
        <div>
          <h1>{user.username}</h1>
          <p>{user.city}, {user.country} · Age {user.age}</p>
          <p className="muted">{user.email}</p>
        </div>
      </section>

      <section className="profile-posts">
        <h2>Your posts</h2>
        {error && <div className="error-card">{error}</div>}
        {!error && posts.length === 0 && <div className="empty-card">You have not posted any videos yet.</div>}
        <div className="feed-list">
          {posts.map((post) => (
            <VideoCard key={post.id} post={post} currentUser={user} onDelete={removeFromList} />
          ))}
        </div>
      </section>
    </main>
  )
}
