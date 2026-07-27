import { useStore } from '../stores/store'

let ws = null
let reconnectAttempts = 0
const MAX_RECONNECT = 5

export const wsService = {
  connect: async (token) => {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const host = window.location.host
      const url = `${protocol}://${host}/ws?token=${token}`
      
      try {
        ws = new WebSocket(url)
        
        ws.onopen = () => {
          console.log('✓ WebSocket conectado')
          useStore.setState({ isConnected: true })
          reconnectAttempts = 0
          resolve()
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            handleMessage(data)
          } catch (e) {
            console.error('Error parsing WebSocket message:', e)
          }
        }
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }
        
        ws.onclose = () => {
          console.log('✗ WebSocket desconectado')
          useStore.setState({ isConnected: false })
          attemptReconnect(token)
        }
      } catch (error) {
        reject(error)
      }
    })
  },

  send: (message) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
      console.log('📤 Mensaje enviado:', message.type)
    } else {
      console.error('❌ WebSocket no está conectado')
    }
  },

  disconnect: () => {
    if (ws) {
      ws.close()
      ws = null
    }
  }
}

const handleMessage = (data) => {
  const { type, payload } = data
  const store = useStore.getState()
  
  console.log('📥 Mensaje recibido:', type)

  switch (type) {
    case 'message': {
      const message = {
        id: Date.now().toString(),
        type: payload.role || 'bot',
        content: payload.content,
        timestamp: new Date().toISOString(),
        phase: payload.phase,
        model: payload.model,
        role_assigned: payload.role_assigned
      }
      store.addMessage(message)
      store.setLoading(false)
      break
    }

    case 'plan': {
      const message = {
        id: Date.now().toString(),
        type: 'plan',
        content: payload.content,
        timestamp: new Date().toISOString(),
        phase: 'planeamiento',
        planData: payload.plan
      }
      store.addMessage(message)
      store.setLoading(false)
      break
    }

    case 'phase_change': {
      store.setPhase(payload.phase)
      if (payload.model) store.setModel(payload.model)
      if (payload.role) store.setRole(payload.role)
      store.setLoading(false)
      break
    }

    case 'error': {
      console.error('Backend error:', payload.message)
      const message = {
        id: Date.now().toString(),
        type: 'error',
        content: `❌ Error: ${payload.message}`,
        timestamp: new Date().toISOString()
      }
      store.addMessage(message)
      store.setLoading(false)
      break
    }

    case 'continue_prompt': {
      // Usuario puede iniciar una nueva solicitud
      store.setLoading(false)
      break
    }

    default:
      console.log('Tipo de mensaje desconocido:', type)
  }
}

const attemptReconnect = (token) => {
  if (reconnectAttempts < MAX_RECONNECT) {
    reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 30000)
    console.log(`⏱️ Reintentando conexión en ${delay}ms... (${reconnectAttempts}/${MAX_RECONNECT})`)
    setTimeout(() => {
      wsService.connect(token).catch(console.error)
    }, delay)
  } else {
    console.error('❌ Máximo número de reconexiones alcanzado')
  }
}
