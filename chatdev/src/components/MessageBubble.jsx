import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'

export default function MessageBubble({ message }) {
  const [showJson, setShowJson] = useState(false)
  const isUser = message.type === 'user'
  const isPlan = message.type === 'plan'
  const phase = message.phase || (isPlan ? 'planeamiento' : 'ejecucion')

  const getPhaseLabel = () => {
    return phase === 'planeamiento' ? '[PLANEAMIENTO]' : '[EJECUCIÓN]'
  }

  const getPhaseColor = () => {
    return phase === 'planeamiento'
      ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
      : 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-md lg:max-w-2xl ${
          isUser
            ? 'bg-blue-600 text-white rounded-3xl rounded-tr-lg'
            : `${getPhaseColor()} border rounded-3xl rounded-tl-lg`
        } px-4 py-3 space-y-2`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 text-xs font-semibold">
            <span className={phase === 'planeamiento' ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400'}>
              {getPhaseLabel()}
            </span>
            {message.model && (
              <span className="text-slate-600 dark:text-slate-400">
                • {message.model}
              </span>
            )}
            {message.role && (
              <span className="text-slate-600 dark:text-slate-400">
                • {message.role}
              </span>
            )}
          </div>
        )}

        <p className={`text-sm whitespace-pre-wrap break-words ${
          isUser ? 'text-white' : 'text-slate-900 dark:text-slate-100'
        }`}>
          {message.content}
        </p>

        {/* JSON Plan Viewer */}
        {isPlan && message.planData && (
          <div className="mt-3 pt-3 border-t border-slate-300 dark:border-slate-600">
            <button
              onClick={() => setShowJson(!showJson)}
              className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            >
              {showJson ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              Ver Plan JSON
            </button>
            {showJson && (
              <pre className="mt-2 p-2 bg-slate-900 dark:bg-slate-800 text-slate-100 text-xs rounded overflow-x-auto max-h-48 overflow-y-auto">
                {JSON.stringify(message.planData, null, 2)}
              </pre>
            )}
          </div>
        )}

        {/* Timestamp */}
        <p className={`text-xs ${
          isUser ? 'text-blue-100' : 'text-slate-600 dark:text-slate-500'
        } mt-1`}>
          {formatDistanceToNow(new Date(message.timestamp), {
            addSuffix: true,
            locale: es
          })}
        </p>
      </div>
    </div>
  )
}
