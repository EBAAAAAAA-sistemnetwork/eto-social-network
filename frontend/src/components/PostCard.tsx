import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'

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

interface CommentData {
  id: string
  author_id: string
  content: string
  created_at: string
  author_name: string
}

export default function PostCard({ post, onDelete }: { post: PostData; onDelete?: (id: string) => void }) {
  const { user } = useAuth()
  const [liked, setLiked] = useState(post.liked_by_me)
  const [likesCount, setLikesCount] = useState(post.likes_count)
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState<CommentData[]>([])
  const [commentText, setCommentText] = useState('')
  const [commentsCount, setCommentsCount] = useState(post.comments_count)

  useEffect(() => {
    if (showComments) {
      api.getComments(post.id).then(setComments)
    }
  }, [showComments, post.id])

  const handleLike = async () => {
    await api.toggleLike(post.id)
    setLiked(!liked)
    setLikesCount(liked ? likesCount - 1 : likesCount + 1)
  }

  const handleComment = async () => {
    if (!commentText.trim()) return
    const c = await api.addComment(post.id, commentText.trim())
    setComments([...comments, c])
    setCommentsCount(commentsCount + 1)
    setCommentText('')
  }

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'только что'
    if (mins < 60) return `${mins} мин назад`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} ч назад`
    const days = Math.floor(hours / 24)
    return `${days} дн назад`
  }

  return (
    <div className="card post-card">
      <div className="post-header">
        <Link to={`/profile/${post.author_id}`}>
          <div className="avatar">
            {post.author_avatar ? <img src={post.author_avatar} alt="" /> : post.author_name[0]}
          </div>
        </Link>
        <div className="post-header-info">
          <Link to={`/profile/${post.author_id}`} className="post-header-name">
            {post.author_name}
          </Link>
          <div className="post-header-time">{timeAgo(post.created_at)}</div>
        </div>
        {user?.id === post.author_id && onDelete && (
          <button className="btn-danger btn-sm" onClick={() => onDelete(post.id)}>
            Удалить
          </button>
        )}
      </div>

      {post.content && <div className="post-content">{post.content}</div>}
      {post.image_url && <img src={post.image_url} alt="" className="post-image" />}

      <div className="post-actions">
        <button className={`post-action ${liked ? 'liked' : ''}`} onClick={handleLike}>
          {liked ? '❤️' : '🤍'} {likesCount}
        </button>
        <button className="post-action" onClick={() => setShowComments(!showComments)}>
          💬 {commentsCount}
        </button>
      </div>

      {showComments && (
        <div className="comments-section">
          {comments.map(c => (
            <div key={c.id} className="comment">
              <div className="comment-header">
                <span className="comment-author">{c.author_name}</span>
                <span className="comment-time">{timeAgo(c.created_at)}</span>
              </div>
              <div className="comment-body">{c.content}</div>
            </div>
          ))}
          <div className="comment-form">
            <input
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              placeholder="Написать комментарий..."
              onKeyDown={e => e.key === 'Enter' && handleComment()}
            />
            <button className="btn-primary btn-sm" onClick={handleComment}>
              Отпр
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
