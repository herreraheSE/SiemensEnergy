import { useEffect, useState } from 'react'
import { useStore } from './stores/store'
import { wsService } from './utils/wsService'
import Sidebar from './components/Sidebar'
import ChatView from './components/ChatView'
import LoginView from './components/LoginView'
import ThemeToggle from './components/ThemeToggle'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const isDarkMode = useStore((state) => state.isDarkMode)

  useEffect(() => {
    // Cargar modo oscuro guardado
    const darkMode = localStorage.getItem('darkMode') === 'true'
    if (darkMode) {
      document.documentElement.classList.add('dark')
    }
    
    // Verificar token guardado
    const token = localStorage.getItem('token')
    if (token) {
      attemptConnect(token)
    } else {
      setIsLoading(false)
    }
  }, [])

  const attemptConnect = async (token) => {
    try {
      await wsService.connect(token)
      setIsAuthenticated(true)
    } catch (error) {
      console.error('Conexión fallida:', error)
      localStorage.removeItem('token')
      setIsAuthenticated(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogin = async (email, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      
      if (!response.ok) throw new Error('Login fallido')
      
      const { token } = await response.json()
      localStorage.setItem('token', token)
      await attemptConnect(token)
    } catch (error) {
      console.error('Error en login:', error)
      alert('Email o contraseña incorrectos')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    wsService.disconnect()
    setIsAuthenticated(false)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Cargando...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginView onLogin={handleLogin} />
  }

  return (
    <div className="flex h-screen bg-white dark:bg-slate-950">
      <Sidebar onLogout={handleLogout} />
      <div className="flex-1 flex flex-col">
        <div className="flex justify-end p-4 border-b border-slate-200 dark:border-slate-800">
          <ThemeToggle />
        </div>
        <ChatView />
      </div>
    </div>
  )
}
