const API_BASE = '/api'

let authToken: string | null = localStorage.getItem('token')

export function setToken(token: string | null) {
  authToken = token
  if (token) {
    localStorage.setItem('token', token)
  } else {
    localStorage.removeItem('token')
  }
}

export function getToken(): string | null {
  return authToken
}

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || 'Ошибка')
  }
  return data
}

export const api = {
  // Auth
  register: (data: { username: string; password: string; display_name: string; email?: string }) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (login: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ login, password }) }),

  getMe: () => request('/auth/me'),

  // Users
  getUser: (id: string) => request(`/users/${id}`),
  searchUsers: (q: string) => request(`/users/search?q=${encodeURIComponent(q)}`),
  updateProfile: (data: any) => request('/users/me', { method: 'PUT', body: JSON.stringify(data) }),
  toggleFriend: (userId: string) => request(`/users/${userId}/friend`, { method: 'POST' }),
  getFriends: (userId: string) => request(`/users/${userId}/friends`),

  // Posts
  getFeed: (skip = 0, limit = 20) => request(`/posts/feed?skip=${skip}&limit=${limit}`),
  getUserPosts: (userId: string, skip = 0, limit = 20) =>
    request(`/posts/user/${userId}?skip=${skip}&limit=${limit}`),
  createPost: (data: { content?: string; image_url?: string }) =>
    request('/posts/', { method: 'POST', body: JSON.stringify(data) }),
  deletePost: (postId: string) => request(`/posts/${postId}`, { method: 'DELETE' }),
  toggleLike: (postId: string) => request(`/posts/${postId}/like`, { method: 'POST' }),
  getComments: (postId: string) => request(`/posts/${postId}/comments`),
  addComment: (postId: string, content: string) =>
    request(`/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify({ content }) }),

  // Messages
  getChats: () => request('/messages/chats'),
  getMessages: (chatId: string, skip = 0) => request(`/messages/${chatId}?skip=${skip}`),
  sendMessage: (recipientId: string, content: string) =>
    request('/messages/send', { method: 'POST', body: JSON.stringify({ recipient_id: recipientId, content }) }),

  // Stories
  getStories: () => request('/stories/feed'),
  createStory: (data: { image_url?: string; caption?: string }) =>
    request('/stories/', { method: 'POST', body: JSON.stringify(data) }),

  // Groups
  getGroups: () => request('/groups/'),
  createGroup: (data: { name: string; description?: string }) =>
    request('/groups/', { method: 'POST', body: JSON.stringify(data) }),
  joinGroup: (groupId: string) => request(`/groups/${groupId}/join`, { method: 'POST' }),
  leaveGroup: (groupId: string) => request(`/groups/${groupId}/leave`, { method: 'POST' }),
  getGroupMembers: (groupId: string) => request(`/groups/${groupId}/members`),
}
