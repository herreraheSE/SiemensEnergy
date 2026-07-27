import { useEffect, useRef, useState } from 'react'
import { useStore } from '../stores/store'
import { wsService } from '../utils/wsService'
import { Send, Zap, AlertCircle, Download } from 'lucide-react'
import MessageBubble from './MessageBubble'
import PhaseIndicator from './PhaseIndicator'

export default function ChatView() {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)
  const currentChatId = useStore((state) => state.currentChatId)
  const messages = useStore((state) => state.messages)
  const addMessage = useStore((state) => state.addMessage)
  const isLoading = useStore((state) => state.isLoading)
  const setLoading = useStore((state) => state.setLoading)
  const currentPhase = useStore((state) => state.currentPhase)
  const isConnected = useStore((state) => state.isConnected)
  const updateChat = useStore((state) => state.updateChat)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (!inputValue.trim() || !currentChatId || !isConnected || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }

    addMessage(userMessage)
    setLoading(true)

    // Enviar al servidor WebSocket
    wsService.send({
      type: 'user_message',
      payload: {
        chatId: currentChatId,
        content: inputValue
      }
    })

    setInputValue('')
    updateChat(currentChatId)
  }

  const handleExport = () => {
    if (messages.length === 0) return

    const content = messages
      .map(msg => {
        let header = `${msg.type.toUpperCase()}`
        if (msg.phase) header += ` [${msg.phase.toUpperCase()}]`
        if (msg.model) header += ` • ${msg.model}`
        return `${header}\n${msg.content}`
      })
      .join('\n\n---\n\n')
    
    const timestamp = new Date().toISOString().split('T')[0]
    const filename = `chatdev-${timestamp}.txt`
    
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content))
    element.setAttribute('download', filename)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  if (!currentChatId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white dark:bg-slate-950">
        <div className="text-center">
          <Zap size={48} className="mx-auto mb-4 text-blue-500 opacity-50" />
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Bienvenido a ChatDev
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
            Crea un nuevo chat para comenzar
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-slate-950">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Chat</h2>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            title="Exportar conversación"
          >
            <Download size={18} />
            Exportar
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle size={32} className="mx-auto mb-3 text-slate-400" />
              <p className="text-slate-600 dark:text-slate-400">
                Comienza escribiendo tu solicitud...
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-center py-4">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Phase Indicator */}
      {currentPhase && <PhaseIndicator />}

      {/* Status Message */}
      {!isConnected && (
        <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
          ⚠️ Desconectado. Intentando reconectar...
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
        <form onSubmit={handleSendMessage} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Escribe tu solicitud..."
            disabled={isLoading || !isConnected}
            className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim() || !isConnected}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  )
}
