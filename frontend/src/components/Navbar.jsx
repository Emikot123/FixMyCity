import { Link, NavLink, useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import Avatar from './Avatar.jsx'

export default function Navbar({ user, setUser }) {
  const navigate = useNavigate()

  async function logout() {
    try {
      await api('/auth/logout', { method: 'POST' })
    } finally {
      setUser(null)
      navigate('/login')
    }
  }

  return (
    <header className="topbar">
      <div className="nav-shell">
        <Link to="/" className="brand">FixMyCity</Link>

        <nav className="nav-links">
          <NavLink to="/">Feed</NavLink>
          {user ? (
            <>
              <NavLink to="/post">Post video</NavLink>
              <NavLink to="/profile" className="profile-link">
                <Avatar user={user} size={30} />
                <span>{user.username}</span>
              </NavLink>
              <button className="link-button" onClick={logout}>Log out</button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/register" className="button-link">Sign up</NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
