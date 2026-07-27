import { useStore } from '../stores/store'
import { Zap, Play } from 'lucide-react'

export default function PhaseIndicator() {
  const currentPhase = useStore((state) => state.currentPhase)
  const currentRole = useStore((state) => state.currentRole)
  const currentModel = useStore((state) => state.currentModel)

  if (!currentPhase) return null

  const isPlanning = currentPhase === 'planeamiento'

  return (
    <div className={`px-4 py-3 border-t ${
      isPlanning
        ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
        : 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
    }`}>
      <div className="flex items-center gap-3">
        {isPlanning ? (
          <Zap className="text-amber-600 dark:text-amber-400" size={20} />
        ) : (
          <Play className="text-green-600 dark:text-green-400" size={20} />
        )}
        <div>
          <p className={`font-semibold ${
            isPlanning
              ? 'text-amber-900 dark:text-amber-100'
              : 'text-green-900 dark:text-green-100'
          }`}>
            {isPlanning ? '[PLANEAMIENTO]' : '[EJECUCIÓN]'}
          </p>
          {currentRole && currentModel && (
            <p className={`text-sm ${
              isPlanning
                ? 'text-amber-700 dark:text-amber-300'
                : 'text-green-700 dark:text-green-300'
            }`}>
              Rol: {currentRole} • Modelo: {currentModel.split('/')[1] || currentModel}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
