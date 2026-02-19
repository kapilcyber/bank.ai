import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { assistantQuery } from '../../config/api'
import './HelpAssistant.css'

const STORAGE_KEY = 'helpAssistantChats'
const MAX_HISTORY = 50

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'Good morning'
  if (hour >= 12 && hour < 17) return 'Good afternoon'
  return 'Good evening'
}

const getInitialMessages = () => [
  { role: 'bot', text: `${getGreeting()}! Welcome to the help assistant.` }
]

const formatReply = (text) => {
  if (!text || typeof text !== 'string') return text
  const parts = text.split(/\*\*(.*?)\*\*/g)
  return parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : p))
}

const getChatTitle = (messages) => {
  const firstUser = messages.find(m => m.role === 'user')
  if (firstUser && firstUser.text) {
    const t = firstUser.text.trim()
    return t.length > 35 ? t.slice(0, 35) + '…' : t
  }
  return 'New chat'
}

const loadHistory = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.slice(0, MAX_HISTORY) : []
  } catch {
    return []
  }
}

const saveHistory = (chats) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chats.slice(0, MAX_HISTORY)))
  } catch {}
}

const HelpAssistant = () => {
  const [open, setOpen] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [currentChatId, setCurrentChatId] = useState(null)
  const [messages, setMessages] = useState(getInitialMessages)
  const [history, setHistory] = useState(loadHistory)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const listRef = useRef(null)

  useEffect(() => {
    if (open && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [open, messages])

  const persistChat = (id, msgs) => {
    const title = getChatTitle(msgs)
    setHistory(prev => {
      const existing = prev.find(c => c.id === id)
      const createdAt = existing ? existing.createdAt : Date.now()
      const without = prev.filter(c => c.id !== id)
      const next = [{ id, title, messages: msgs, createdAt }, ...without]
      saveHistory(next)
      return next
    })
  }

  const startNewChat = () => {
    const hasUserMessages = messages.some(m => m.role === 'user')
    if (hasUserMessages && currentChatId) {
      const existing = history.find(c => c.id === currentChatId)
      if (existing) {
        const updated = history.map(c => c.id === currentChatId ? { ...c, messages } : c)
        saveHistory(updated)
      } else {
        const id = `chat-${Date.now()}`
        persistChat(id, messages)
      }
    } else if (hasUserMessages && !currentChatId) {
      const id = `chat-${Date.now()}`
      persistChat(id, messages)
    }
    setCurrentChatId(null)
    setMessages(getInitialMessages())
    setShowHistory(false)
  }

  const openPastChat = (chat) => {
    setCurrentChatId(chat.id)
    setMessages(chat.messages && chat.messages.length ? chat.messages : getInitialMessages())
    setShowHistory(false)
  }

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || loading) return

    setInput('')
    const userMsg = { role: 'user', text: msg }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await assistantQuery(msg)
      const reply = res?.reply || "I couldn't get a response. Please try again."
      setMessages(prev => {
        const next = [...prev, { role: 'bot', text: reply }]
        const id = currentChatId || `chat-${Date.now()}`
        if (!currentChatId) setCurrentChatId(id)
        persistChat(id, next)
        return next
      })
    } catch (err) {
      const errMsg = err?.message || err?.detail || 'Something went wrong. Please try again.'
      setMessages(prev => {
        const next = [...prev, { role: 'bot', text: errMsg, error: true }]
        const id = currentChatId || `chat-${Date.now()}`
        if (!currentChatId) setCurrentChatId(id)
        persistChat(id, next)
        return next
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const content = (
    <>
      <button
        type="button"
        className={`help-assistant-fab ${open ? 'help-assistant-fab--open' : 'help-assistant-fab--flying'}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close help assistant' : 'Open help assistant'}
      >
        {open ? (
          <span className="help-assistant-fab-close" aria-hidden>×</span>
        ) : (
          <span className="help-assistant-fab-bird" aria-hidden>
            <svg viewBox="0 0 32 32" fill="currentColor" className="help-assistant-bird-svg">
              <ellipse cx="16" cy="18" rx="6" ry="8" />
              <circle cx="16" cy="10" r="4" />
              <path className="help-assistant-bird-wing help-assistant-bird-wing--left" d="M10 14 Q4 16 8 20 Q12 18 10 14Z" />
              <path className="help-assistant-bird-wing help-assistant-bird-wing--right" d="M22 14 Q28 16 24 20 Q20 18 22 14Z" />
              <circle cx="18" cy="10" r="1" fill="currentColor" opacity="0.8" />
            </svg>
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="help-assistant-panel"
            initial={{ opacity: 0, y: 20, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.96 }}
            transition={{ duration: 0.2 }}
          >
            <div className="help-assistant-header">
              <span className="help-assistant-title">Help Assistant</span>
              <div className="help-assistant-header-actions">
                <button type="button" className="help-assistant-btn-icon" onClick={startNewChat} title="New chat">
                  New chat
                </button>
                <button type="button" className="help-assistant-btn-icon" onClick={() => setShowHistory(h => !h)} title="Chat history">
                  History
                </button>
                <button type="button" className="help-assistant-close" onClick={() => setOpen(false)} aria-label="Close">
                  {'\u2715'}
                </button>
              </div>
            </div>

            {showHistory ? (
              <div className="help-assistant-history">
                <p className="help-assistant-history-title">Past chats</p>
                {history.length === 0 ? (
                  <p className="help-assistant-history-empty">No past chats. Start a conversation and it will appear here.</p>
                ) : (
                  <ul className="help-assistant-history-list">
                    {history.map(chat => (
                      <li key={chat.id}>
                        <button type="button" className="help-assistant-history-item" onClick={() => openPastChat(chat)}>
                          <span className="help-assistant-history-item-title">{chat.title || 'Chat'}</span>
                          <span className="help-assistant-history-item-date">
                            {chat.createdAt ? new Date(chat.createdAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <>
                <div className="help-assistant-messages" ref={listRef}>
                  {messages.map((item, i) => (
                    <div key={i} className={`help-assistant-bubble help-assistant-bubble-${item.role}`}>
                      <div className="help-assistant-bubble-inner">
                        {item.role === 'bot' ? formatReply(item.text) : item.text}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="help-assistant-bubble help-assistant-bubble-bot">
                      <div className="help-assistant-bubble-inner help-assistant-typing">Thinking…</div>
                    </div>
                  )}
                </div>

                <div className="help-assistant-footer">
                  <input
                    type="text"
                    className="help-assistant-input"
                    placeholder="Ask about the platform, skills, employee list…"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="help-assistant-send"
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                  >
                    Send
                  </button>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )

  return createPortal(content, document.body)
}

export default HelpAssistant
