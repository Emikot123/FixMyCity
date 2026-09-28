import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { api } from './api.js'
import Navbar from './components/Navbar.jsx'
import CreatePost from './pages/CreatePost.jsx'
import Feed from './pages/Feed.jsx'
import Login from './pages/Login.jsx'
import Profile from './pages/Profile.jsx'
import Register from './pages/Register.jsx'
import Verify from './pages/Verify.jsx'

export default function App() {
  const [user, setUser] = useState(null)
  const [authReady, setAuthReady] = useState(false)

  useEffect(() => {
    api('/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setAuthReady(true))
  }, [])

  if (!authReady) {
    return <div className="app-loading">Loading FixMyCity…</div>
  }

  return (
    <>
      <Navbar user={user} setUser={setUser} />
      <Routes>
        <Route path="/" element={<Feed user={user} />} />
        <Route path="/login" element={<Login user={user} />} />
        <Route path="/register" element={<Register user={user} />} />
        <Route path="/verify" element={<Verify setUser={setUser} />} />
        <Route path="/post" element={<CreatePost user={user} />} />
        <Route path="/profile" element={<Profile user={user} />} />
        <Route path="*" element={<Feed user={user} />} />
      </Routes>
    </>
  )
}
