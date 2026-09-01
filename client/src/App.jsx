import { useState, useEffect, useRef } from 'react'
import ChatMessage from './components/ChatMessage'
import ModelSelector from './components/ModelSelector'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [ollamaAvailable, setOllamaAvailable] = useState(false)
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  // Load chat history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('chatHistory')
    if (saved) {
      try {
        setMessages(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to load chat history:', e)
      }
    }
  }, [])

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages))
  }, [messages])

  // Fetch available models on mount
  useEffect(() => {
    fetchModels()
    checkOllamaHealth()
  }, [])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkOllamaHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      const data = await response.json()
      setOllamaAvailable(data.ollama_available)
      setError(null)
    } catch (err) {
      setOllamaAvailable(false)
      setError('Backend server not available. Make sure the Python server is running.')
    }
  }

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`)
      const data = await response.json()
      setModels(data.models || [])
      if (data.models && data.models.length > 0) {
        setSelectedModel(data.models[0].name)
      }
      setError(null)
    } catch (err) {
      setError('Failed to fetch models. Is the backend running?')
      console.error('Error fetching models:', err)
    }
  }

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setLoading(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || !selectedModel || loading) return

    if (!ollamaAvailable) {
      setError('Ollama is not available. Please start Ollama and refresh the page.')
      return
    }

    const userMessage = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: abortControllerRef.current.signal,
          body: JSON.stringify({
            model: selectedModel,
            messages: [...messages, userMessage]
          })
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const chunk = JSON.parse(line.slice(6))
              if (chunk.message && chunk.message.content) {
                assistantContent += chunk.message.content
                setMessages(prev => {
                  const updated = [...prev]
                  if (updated[updated.length - 1].role === 'assistant') {
                    updated[updated.length - 1].content = assistantContent
                  } else {
                    updated.push({ role: 'assistant', content: assistantContent })
                  }
                  return updated
                })
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Generation stopped by user')
      } else {
        console.error('Error sending message:', err)
        setError(
          err.message ||
            'Failed to get response from model'
        )
      }
    } finally {
      setLoading(false)
    }
  }

  const clearChat = () => {
    if (window.confirm('Clear chat history?')) {
      setMessages([])
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <img src="/chibot_icon.png" alt="Chibot" className="chibot-icon" />
          <h1>Chibot</h1>
        </div>
        <ModelSelector
          models={models}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          loading={loading}
        />
      </header>

      {error && <div className="error-banner">{error}</div>}

      {!ollamaAvailable && (
        <div className="warning-banner">
          ⚠️ Ollama is not running. Please start Ollama to use the chat.
        </div>
      )}

      <div className="chat-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Welcome! Start a conversation with the AI assistant.</p>
            <p>Select a model and type your message below.</p>
          </div>
        )}

        <div className="messages">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))}
          {loading && (
            <div className="message assistant-message">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
          <div className="chat-spacer" />
        </div>

        <form className="chat-form" onSubmit={handleSendMessage}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSendMessage(e)
            }
          }}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={loading || !ollamaAvailable}
          rows="3"
        />
        <div className="form-actions">
          {loading ? (
            <button
              type="button"
              onClick={handleStopGeneration}
              className="send-button"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || !ollamaAvailable || !selectedModel}
              className="send-button"
            >
              Send
            </button>
          )}
          <button
            type="button"
            onClick={clearChat}
            disabled={messages.length === 0 || loading}
            className="clear-button"
          >
            Clear
          </button>
        </div>
      </form>
      </div>
    </div>
  )
}

export default App
