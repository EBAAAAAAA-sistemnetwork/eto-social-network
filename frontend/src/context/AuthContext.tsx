import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api, setToken, getToken } from '../api'

interface User {
  id: string
  username: string
  display_name: string
  avatar_url: string | null
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: { username: string; password: string; display_name: string; email?: string }) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (token) {
      api.getMe()
        .then(u => setUser(u))
        .catch(() => { setToken(null); setUser(null) })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const data = await api.login(username, password)
    setToken(data.access_token)
    setUser(data.user)
  }

  const register = async (regData: { username: string; password: string; display_name: string }) => {
    await api.register(regData)
    await login(regData.username, regData.password)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
