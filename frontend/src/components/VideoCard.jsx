import { useState } from 'react'
import { api, mediaUrl } from '../api.js'
import Avatar from './Avatar.jsx'

export default function VideoCard({ post, currentUser, onDelete }) {
  const [likes, setLikes] = useState(post.likes)
  const [liked, setLiked] = useState(post.liked_by_me)
  const [busy, setBusy] = useState(false)

  async function toggleLike() {
    if (!currentUser || busy) return
    setBusy(true)
    try {
      const data = await api(`/posts/${post.id}/like`, { method: 'POST' })
      setLikes(data.likes)
      setLiked(data.liked)
    } catch (error) {
      window.alert(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function removePost() {
    if (!window.confirm('Delete this post?')) return
    try {
      await api(`/me/posts/${post.id}`, { method: 'DELETE' })
      onDelete?.(post.id)
    } catch (error) {
      window.alert(error.message)
    }
  }

  return (
    <article className="video-card">
      <div className="post-author-row">
        <Avatar user={post.user} />
        <div>
          <strong>{post.user.username}</strong>
          <div className="muted small">{post.city}, {post.country}</div>
        </div>
      </div>

      <video className="post-video" controls preload="metadata" src={mediaUrl(post.video_url)} />

      <div className="post-body">
        <h2>{post.title}</h2>
        <p>{post.details}</p>
        <div className="post-actions">
          <button
            className={liked ? 'like-button liked' : 'like-button'}
            onClick={toggleLike}
            disabled={!currentUser || busy}
            title={currentUser ? 'Like this post' : 'Log in to like'}
          >
            {liked ? 'Liked' : 'Like'} · {likes}
          </button>
          {currentUser?.id === post.user.id && onDelete && (
            <button className="danger-link" onClick={removePost}>Delete</button>
          )}
        </div>
      </div>
    </article>
  )
}
