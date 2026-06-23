import { useState, useEffect } from 'react'
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

interface StoryData {
  id: string
  user_id: string
  image_url: string | null
  video_url: string | null
  caption: string | null
  created_at: string
  user_name: string
  user_avatar: string | null
}

export default function Feed() {
  const { user } = useAuth()
  const [posts, setPosts] = useState<PostData[]>([])
  const [stories, setStories] = useState<StoryData[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)

  const loadFeed = async () => {
    const p = await api.getFeed()
    setPosts(p)
    setLoading(false)
  }

  useEffect(() => {
    loadFeed()
    api.getStories().then(setStories)
  }, [])

  const handleCreatePost = async () => {
    if (!content.trim()) return
    const newPost = await api.createPost({ content: content.trim() })
    setPosts([newPost, ...posts])
    setContent('')
  }

  const handleDeletePost = async (postId: string) => {
    await api.deletePost(postId)
    setPosts(posts.filter(p => p.id !== postId))
  }

  return (
    <div className="container">
      {stories.length > 0 && (
        <div className="stories-bar">
          {stories.map(s => (
            <div key={s.id} className="story-item">
              <div className="story-ring">
                <div className="avatar" style={{ width: '100%', height: '100%' }}>
                  {s.user_avatar ? <img src={s.user_avatar} alt="" /> : s.user_name[0]}
                </div>
              </div>
              <span className="story-name">{s.user_name}</span>
            </div>
          ))}
        </div>
      )}

      <div className="card create-post">
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder={`Что нового, ${user?.display_name}?`}
        />
        <div className="create-post-actions">
          <span style={{ color: 'var(--text2)', fontSize: 13 }}>Поделись с друзьями</span>
          <button className="btn-primary btn-sm" onClick={handleCreatePost}>
            Опубликовать
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : posts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <div className="empty-state-text">Пока нет постов. Добавь друзей или напиши первый пост!</div>
        </div>
      ) : (
        posts.map(p => <PostCard key={p.id} post={p} onDelete={handleDeletePost} />)
      )}
    </div>
  )
}
