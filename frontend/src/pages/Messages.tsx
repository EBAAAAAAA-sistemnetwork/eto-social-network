import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'
import { useNavigate } from 'react-router-dom'

interface ChatItemData {
  chat_id: string
  other_user_id: string
  other_user_name: string
  other_user_avatar: string | null
  last_message: string | null
  last_message_time: string | null
  unread_count: number
}

interface MessageData {
  id: string
  chat_id: string
  sender_id: string
  content: string | null
  image_url: string | null
  created_at: string
  is_read: boolean
  sender_name: string
}

export default function Messages() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [chats, setChats] = useState<ChatItemData[]>([])
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const [messages, setMessages] = useState<MessageData[]>([])
  const [text, setText] = useState('')
  const [chatUser, setChatUser] = useState<ChatItemData | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const loadChats = async () => {
    const c = await api.getChats()
    setChats(c)
  }

  useEffect(() => {
    loadChats()
    const interval = setInterval(loadChats, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!activeChat) return
    api.getMessages(activeChat).then(setMessages)
    const interval = setInterval(async () => {
      const ms = await api.getMessages(activeChat)
      setMessages(ms)
    }, 3000)
    return () => clearInterval(interval)
  }, [activeChat])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const openChat = (chatId: string) => {
    setActiveChat(chatId)
    const c = chats.find(ch => ch.chat_id === chatId)
    setChatUser(c || null)
  }

  const handleSend = async () => {
    if (!text.trim() || !chatUser) return
    const msg = await api.sendMessage(chatUser.other_user_id, text.trim())
    setMessages([...messages, msg])
    setText('')
    loadChats()
  }

  const handleSearch = async () => {
    if (searchQuery.length < 2) return
    const r = await api.searchUsers(searchQuery)
    setSearchResults(r)
  }

  const startChat = async (otherUserId: string) => {
    const chatId = [user!.id, otherUserId].sort().join('_')
    setTimeout(() => loadChats(), 500)
    openChat(chatId)
    setSearchResults([])
    setSearchQuery('')
  }

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'сейчас'
    if (mins < 60) return `${mins}м`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}ч`
    return `${Math.floor(hours / 24)}д`
  }

  return (
    <div className="chat-layout">
      <div className="chat-sidebar">
        <div style={{ padding: '12px 16px' }}>
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Поиск людей..."
          />
          {searchResults.length > 0 && (
            <div style={{ marginTop: 4 }}>
              {searchResults.map((r: any) => (
                <div
                  key={r.id}
                  className="search-result"
                  onClick={() => {
                    if (r.id !== user!.id) startChat(r.id)
                  }}
                  style={{ cursor: 'pointer', padding: '8px 12px' }}
                >
                  <div className="avatar avatar-sm">
                    {r.avatar_url ? <img src={r.avatar_url} alt="" /> : r.display_name[0]}
                  </div>
                  <span style={{ fontSize: 14 }}>{r.display_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        {chats.length === 0 ? (
          <div className="empty-state" style={{ padding: 40 }}>
            <div className="empty-state-text">Нет сообщений</div>
          </div>
        ) : (
          chats.map(c => (
            <div
              key={c.chat_id}
              className={`chat-item ${c.chat_id === activeChat ? 'active' : ''}`}
              onClick={() => openChat(c.chat_id)}
            >
              <div className="avatar avatar-sm">
                {c.other_user_avatar ? <img src={c.other_user_avatar} alt="" /> : c.other_user_name[0]}
              </div>
              <div className="chat-item-info">
                <div className="chat-item-name">{c.other_user_name}</div>
                <div className="chat-item-last">
                  {c.last_message || 'Нет сообщений'}
                </div>
              </div>
              {c.unread_count > 0 && (
                <span className="chat-item-badge">{c.unread_count}</span>
              )}
            </div>
          ))
        )}
      </div>

      <div className="chat-main">
        {!activeChat ? (
          <div className="empty-state" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div>
              <div className="empty-state-icon">💬</div>
              <div className="empty-state-text">Выбери чат или найди пользователя</div>
            </div>
          </div>
        ) : (
          <>
            <div className="chat-header">
              <div className="avatar avatar-sm" style={{ cursor: 'pointer' }} onClick={() => chatUser && navigate(`/profile/${chatUser.other_user_id}`)}>
                {chatUser?.other_user_avatar ? <img src={chatUser.other_user_avatar} alt="" /> : (chatUser?.other_user_name[0] || '?')}
              </div>
              {chatUser?.other_user_name}
            </div>
            <div className="chat-messages">
              {messages.map(m => (
                <div
                  key={m.id}
                  className={`chat-bubble ${m.sender_id === user?.id ? 'chat-bubble-mine' : 'chat-bubble-other'}`}
                >
                  <div>{m.content}</div>
                  <div style={{ fontSize: 10, opacity: 0.6, marginTop: 4 }}>
                    {timeAgo(m.created_at)}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input">
              <input
                value={text}
                onChange={e => setText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Сообщение..."
              />
              <button className="btn-primary btn-sm" onClick={handleSend}>Отпр</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
