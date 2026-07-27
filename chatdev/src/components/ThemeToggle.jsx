import { Moon, Sun } from 'lucide-react'
import { useStore } from '../stores/store'

export default function ThemeToggle() {
  const isDarkMode = useStore((state) => state.isDarkMode)
  const setDarkMode = useStore((state) => state.setDarkMode)

  return (
    <button
      onClick={() => setDarkMode(!isDarkMode)}
      className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
      title={isDarkMode ? 'Modo claro' : 'Modo oscuro'}
    >
      {isDarkMode ? (
        <Sun size={20} className="text-yellow-500" />
      ) : (
        <Moon size={20} className="text-slate-600" />
      )}
    </button>
  )
}
