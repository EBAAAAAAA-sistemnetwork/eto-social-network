import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'

interface GroupData {
  id: string
  name: string
  description: string | null
  avatar_url: string | null
  is_public: boolean
  owner_id: string
  created_at: string
  members_count: number
}

interface MemberData {
  id: string
  username: string
  display_name: string
  avatar_url: string | null
  role: string
}

export default function Groups() {
  const { user } = useAuth()
  const [groups, setGroups] = useState<GroupData[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [selectedGroup, setSelectedGroup] = useState<GroupData | null>(null)
  const [members, setMembers] = useState<MemberData[]>([])

  const loadGroups = async () => {
    const g = await api.getGroups()
    setGroups(g)
    setLoading(false)
  }

  useEffect(() => {
    loadGroups()
  }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    await api.createGroup({ name: newName.trim(), description: newDesc.trim() || undefined })
    setNewName('')
    setNewDesc('')
    setShowCreate(false)
    loadGroups()
  }

  const handleJoin = async (groupId: string) => {
    await api.joinGroup(groupId)
    loadGroups()
  }

  const handleLeave = async (groupId: string) => {
    await api.leaveGroup(groupId)
    loadGroups()
    if (selectedGroup?.id === groupId) {
      setSelectedGroup(null)
      setMembers([])
    }
  }

  const openGroup = async (group: GroupData) => {
    setSelectedGroup(group)
    const m = await api.getGroupMembers(group.id)
    setMembers(m)
  }

  if (loading) return <div className="loading">Загрузка...</div>

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700 }}>Группы</h2>
        <button className="btn-primary btn-sm" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? 'Отмена' : 'Создать группу'}
        </button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="form-group">
            <label>Название группы</label>
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="Название..."
            />
          </div>
          <div className="form-group">
            <label>Описание</label>
            <textarea
              value={newDesc}
              onChange={e => setNewDesc(e.target.value)}
              placeholder="О чём группа..."
            />
          </div>
          <button className="btn-primary" onClick={handleCreate}>Создать</button>
        </div>
      )}

      {selectedGroup ? (
        <>
          <button
            className="btn-outline btn-sm"
            onClick={() => { setSelectedGroup(null); setMembers([]) }}
            style={{ marginBottom: 12 }}
          >
            ← Назад к группам
          </button>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3>{selectedGroup.name}</h3>
            {selectedGroup.description && (
              <p style={{ color: 'var(--text2)', fontSize: 14, marginTop: 8 }}>{selectedGroup.description}</p>
            )}
            <p style={{ fontSize: 13, color: 'var(--text2)', marginTop: 8 }}>
              Участников: {selectedGroup.members_count}
            </p>
            {selectedGroup.owner_id === user?.id ? (
              <span style={{ fontSize: 13, color: 'var(--primary)' }}>Вы создатель</span>
            ) : members.some(m => m.id === user?.id) ? (
              <button className="btn-outline btn-sm" onClick={() => handleLeave(selectedGroup.id)}>
                Покинуть
              </button>
            ) : (
              <button className="btn-primary btn-sm" onClick={() => handleJoin(selectedGroup.id)}>
                Вступить
              </button>
            )}
          </div>

          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Участники ({members.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {members.map(m => (
              <div key={m.id} className="search-result">
                <div className="avatar avatar-sm">
                  {m.avatar_url ? <img src={m.avatar_url} alt="" /> : m.display_name[0]}
                </div>
                <div>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{m.display_name}</span>
                  {m.role === 'owner' && (
                    <span style={{ fontSize: 11, color: 'var(--primary)', marginLeft: 8 }}>Создатель</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <>
          {groups.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <div className="empty-state-text">Нет групп. Создай первую!</div>
            </div>
          ) : (
            groups.map(g => (
              <div
                key={g.id}
                className="card"
                style={{ marginBottom: 12, cursor: 'pointer' }}
                onClick={() => openGroup(g)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{g.name}</div>
                    {g.description && (
                      <div style={{ fontSize: 13, color: 'var(--text2)', marginTop: 4 }}>
                        {g.description.length > 100 ? g.description.slice(0, 100) + '...' : g.description}
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: 13, color: 'var(--text2)', whiteSpace: 'nowrap' }}>
                    {g.members_count} уч.
                  </span>
                </div>
              </div>
            ))
          )}
        </>
      )}
    </div>
  )
}
