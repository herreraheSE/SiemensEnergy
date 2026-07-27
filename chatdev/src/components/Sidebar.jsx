import { Plus, MessageSquare, Trash2, LogOut } from 'lucide-react'
import { useStore } from '../stores/store'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'

export default function Sidebar({ onLogout }) {
  const chats = useStore((state) => state.chats)
  const currentChatId = useStore((state) => state.currentChatId)
  const createChat = useStore((state) => state.createChat)
  const loadChat = useStore((state) => state.loadChat)
  const deleteChat = useStore((state) => state.deleteChat)

  const handleNewChat = () => {
    createChat(`Chat - ${new Date().toLocaleDateString()}`)
  }

  return (
    <div className="w-64 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition-colors"
        >
          <Plus size={20} />
          Nuevo Chat
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {chats.length === 0 ? (
          <p className="text-slate-500 dark:text-slate-400 text-sm text-center py-8">
            No hay chats
          </p>
        ) : (
          chats.map((chat) => (
            <div
              key={chat.id}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                currentChatId === chat.id
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100'
                  : 'hover:bg-slate-200 dark:hover:bg-slate-800'
              }`}
            >
              <MessageSquare size={18} className="flex-shrink-0" />
              <div
                className="flex-1 min-w-0"
                onClick={() => loadChat(chat.id)}
              >
                <p className="text-sm font-medium truncate">{chat.title}</p>
                <p className="text-xs opacity-70 truncate">
                  {formatDistanceToNow(new Date(chat.createdAt), {
                    addSuffix: true,
                    locale: es
                  })}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteChat(chat.id)
                }}
                className="p-1 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 font-medium py-2 rounded-lg transition-colors"
        >
          <LogOut size={18} />
          Cerrar Sesión
        </button>
      </div>
    </div>
  )
}
