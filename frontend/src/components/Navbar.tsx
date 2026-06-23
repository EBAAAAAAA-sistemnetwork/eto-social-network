import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">ЭТО</Link>
      <div className="navbar-links">
        <Link to="/">Лента</Link>
        <Link to="/messages">Сообщения</Link>
        <Link to="/groups">Группы</Link>
        <Link to={`/profile/${user?.id}`} className="navbar-user">
          <div className="avatar avatar-sm">
            {user?.avatar_url ? <img src={user.avatar_url} alt="" /> : (user?.display_name?.[0] || '?')}
          </div>
          {user?.display_name}
        </Link>
        <button onClick={handleLogout}>Выйти</button>
      </div>
    </nav>
  )
}
