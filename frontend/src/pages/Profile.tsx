import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'
import PostCard from '../components/PostCard'

interface PostData {
  id: string
  author_id: string
  content: string | null
  image_url: string | null
  video_url: string | null
  created_at: string
  updated_at: string
  author_name: string
  author_avatar: string | null
  likes_count: number
  comments_count: number
  liked_by_me: boolean
}

interface ProfileData {
  id: string
  username: string
  display_name: string
  email: string | null
  phone: string | null
  avatar_url: string | null
  bio: string | null
  status: string | null
  is_online: boolean
  last_seen: string
  created_at: string
  friends_count: number
  posts_count: number
}

interface FriendData {
  id: string
  username: string
  display_name: string
  avatar_url: string | null
  is_online: boolean
}

export default function Profile() {
  const { userId } = useParams<{ userId: string }>()
  const { user: me } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [posts, setPosts] = useState<PostData[]>([])
  const [friends, setFriends] = useState<FriendData[]>([])
  const [isFriend, setIsFriend] = useState(false)
  const [tab, setTab] = useState<'posts' | 'friends'>('posts')
  const [loading, setLoading] = useState(true)

  const isMe = me?.id === userId

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    Promise.all([
      api.getUser(userId).then(setProfile),
      api.getUserPosts(userId).then(setPosts),
      api.getFriends(userId).then(fs => {
        setFriends(fs)
        if (!isMe) setIsFriend(fs.some((f: FriendData) => f.id === me?.id))
      }),
    ]).finally(() => setLoading(false))
  }, [userId])

  const handleToggleFriend = async () => {
    if (!userId) return
    const res = await api.toggleFriend(userId)
    setIsFriend(res.status === 'added')
  }

  const handleDeletePost = async (postId: string) => {
    await api.deletePost(postId)
    setPosts(posts.filter(p => p.id !== postId))
  }

  if (loading) return <div className="loading">Загрузка...</div>
  if (!profile) return <div className="empty-state">Пользователь не найден</div>

  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="profile-header">
          <div className="avatar avatar-lg">
            {profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : profile.display_name[0]}
          </div>
          <div className="profile-info">
            <div className="profile-name">
              {profile.display_name}
              {profile.is_online && <span className="online-dot" />}
            </div>
            <div className="profile-username">@{profile.username}</div>
            {profile.bio && <div className="profile-bio">{profile.bio}</div>}
            {profile.status && (
              <div style={{ fontSize: 13, color: 'var(--primary)', marginTop: 4 }}>
                {profile.status}
              </div>
            )}
            <div className="profile-stats">
              <div className="profile-stat">
                <div className="profile-stat-num">{profile.posts_count}</div>
                <div className="profile-stat-label">Постов</div>
              </div>
              <div className="profile-stat" style={{ cursor: 'pointer' }} onClick={() => setTab('friends')}>
                <div className="profile-stat-num">{profile.friends_count}</div>
                <div className="profile-stat-label">Друзей</div>
              </div>
            </div>
          </div>
          {!isMe && (
            <button className={isFriend ? 'btn-outline' : 'btn-primary'} onClick={handleToggleFriend}>
              {isFriend ? 'Удалить из друзей' : 'Добавить в друзья'}
            </button>
          )}
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'posts' ? 'active' : ''}`} onClick={() => setTab('posts')}>
          Посты
        </button>
        <button className={`tab ${tab === 'friends' ? 'active' : ''}`} onClick={() => setTab('friends')}>
          Друзья
        </button>
        {isMe && (
          <button className="tab" onClick={() => navigate('/')}>
            Поиск людей
          </button>
        )}
      </div>

      {tab === 'posts' && (
        <>
          {posts.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <div className="empty-state-text">Нет постов</div>
            </div>
          ) : (
            posts.map(p => <PostCard key={p.id} post={p} onDelete={isMe ? handleDeletePost : undefined} />)
          )}
        </>
      )}

      {tab === 'friends' && (
        <>
          <SearchBar />
          {friends.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <div className="empty-state-text">Нет друзей</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {friends.map(f => (
                <div
                  key={f.id}
                  className="search-result"
                  onClick={() => navigate(`/profile/${f.id}`)}
                >
                  <div className="avatar avatar-sm">
                    {f.avatar_url ? <img src={f.avatar_url} alt="" /> : f.display_name[0]}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {f.display_name}
                      {f.is_online && <span className="online-dot" />}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text2)' }}>@{f.username}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function SearchBar() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    if (query.length < 2) {
      setResults([])
      return
    }
    const timer = setTimeout(async () => {
      const r = await api.searchUsers(query)
      setResults(r)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  return (
    <div style={{ marginBottom: 16 }}>
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Поиск по имени..."
      />
      {results.length > 0 && (
        <div className="card" style={{ marginTop: 4, padding: 8 }}>
          {results.map((r: any) => (
            <div
              key={r.id}
              className="search-result"
              onClick={() => {
                navigate(`/profile/${r.id}`)
                setQuery('')
                setResults([])
              }}
            >
              <div className="avatar avatar-sm">
                {r.avatar_url ? <img src={r.avatar_url} alt="" /> : r.display_name[0]}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{r.display_name}</div>
                <div style={{ fontSize: 12, color: 'var(--text2)' }}>@{r.username}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
