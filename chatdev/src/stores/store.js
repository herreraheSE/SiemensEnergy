import { create } from 'zustand'

export const useStore = create((set) => ({
  // UI State
  isDarkMode: localStorage.getItem('darkMode') === 'true',
  setDarkMode: (mode) => {
    localStorage.setItem('darkMode', mode)
    set({ isDarkMode: mode })
    if (mode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  },

  // Chat State
  chats: [],
  currentChatId: null,
  messages: [],
  isConnected: false,
  currentPhase: null, // 'planeamiento' | 'ejecucion'
  currentRole: null,
  currentModel: null,
  isLoading: false,

  // Actions
  setConnected: (status) => set({ isConnected: status }),
  setLoading: (status) => set({ isLoading: status }),
  setPhase: (phase) => set({ currentPhase: phase }),
  setRole: (role) => set({ currentRole: role }),
  setModel: (model) => set({ currentModel: model }),

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  createChat: (title) => {
    const chatId = Date.now().toString()
    const newChat = {
      id: chatId,
      title,
      createdAt: new Date().toISOString(),
      messages: []
    }
    set((state) => ({
      chats: [newChat, ...state.chats],
      currentChatId: chatId,
      messages: []
    }))
    return chatId
  },

  loadChat: (chatId) => {
    set((state) => {
      const chat = state.chats.find(c => c.id === chatId)
      return {
        currentChatId: chatId,
        messages: chat?.messages || []
      }
    })
  },

  deleteChat: (chatId) => set((state) => ({
    chats: state.chats.filter(c => c.id !== chatId),
    currentChatId: state.currentChatId === chatId ? null : state.currentChatId,
    messages: state.currentChatId === chatId ? [] : state.messages
  })),

  updateChat: (chatId) => set((state) => {
    const chats = state.chats.map(c => 
      c.id === chatId ? { ...c, messages: state.messages } : c
    )
    return { chats }
  })
}))
