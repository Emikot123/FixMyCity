import { mediaUrl } from '../api.js'

export default function Avatar({ user, size = 38 }) {
  const style = { width: size, height: size }

  if (user?.profile_picture_url) {
    return (
      <img
        className="avatar"
        style={style}
        src={mediaUrl(user.profile_picture_url)}
        alt={`${user.username} profile`}
      />
    )
  }

  return (
    <div className="avatar avatar-fallback" style={style} aria-label={`${user?.username || 'User'} profile`}>
      {(user?.username || '?').slice(0, 1).toUpperCase()}
    </div>
  )
}
