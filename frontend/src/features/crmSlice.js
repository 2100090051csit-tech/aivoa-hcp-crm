import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

const API_BASE = '/api'

// Async Thunks
export const fetchHcps = createAsyncThunk('crm/fetchHcps', async () => {
  const response = await fetch(`${API_BASE}/hcps`)
  if (!response.ok) throw new Error('Failed to fetch HCPs')
  return await response.json()
})

export const fetchHcpDetails = createAsyncThunk('crm/fetchHcpDetails', async (hcpId) => {
  const response = await fetch(`${API_BASE}/hcps/${hcpId}`)
  if (!response.ok) throw new Error('Failed to fetch HCP details')
  return await response.json()
})

export const fetchInteractions = createAsyncThunk('crm/fetchInteractions', async () => {
  const response = await fetch(`${API_BASE}/interactions`)
  if (!response.ok) throw new Error('Failed to fetch interactions')
  return await response.json()
})

export const addInteraction = createAsyncThunk('crm/addInteraction', async (interactionData) => {
  const response = await fetch(`${API_BASE}/interactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(interactionData)
  })
  if (!response.ok) throw new Error('Failed to log interaction')
  return await response.json()
})

export const fetchProducts = createAsyncThunk('crm/fetchProducts', async () => {
  const response = await fetch(`${API_BASE}/products`)
  if (!response.ok) throw new Error('Failed to fetch products')
  return await response.json()
})

export const fetchFollowups = createAsyncThunk('crm/fetchFollowups', async () => {
  const response = await fetch(`${API_BASE}/followups`)
  if (!response.ok) throw new Error('Failed to fetch followups')
  return await response.json()
})

export const toggleFollowup = createAsyncThunk('crm/toggleFollowup', async (followupId) => {
  const response = await fetch(`${API_BASE}/followups/${followupId}/toggle`, {
    method: 'PUT'
  })
  if (!response.ok) throw new Error('Failed to toggle followup status')
  return await response.json()
})

export const sendChatMessage = createAsyncThunk(
  'crm/sendChatMessage',
  async ({ message, history, userId = 1 }) => {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, user_id: userId })
    })
    if (!response.ok) throw new Error('Failed to communicate with AI Agent')
    return await response.json()
  }
)

const crmSlice = createSlice({
  name: 'crm',
  initialState: {
    hcps: [],
    selectedHcp: null,
    interactions: [],
    products: [],
    followups: [],
    chatHistory: [
      {
        role: 'assistant',
        content: 'Hello! I am your AI CRM Assistant. You can describe your doctor interaction here, e.g., "Met Dr. Jenkins regarding Keytruda today, she was highly positive and requested trial details next week." I will decode the entities, save the interaction, and schedule tasks automatically!'
      }
    ],
    status: 'idle',
    chatLoading: false,
    error: null
  },
  reducers: {
    clearChat: (state) => {
      state.chatHistory = [
        {
          role: 'assistant',
          content: 'Hello! I am your AI CRM Assistant. You can describe your doctor interaction here, e.g., "Met Dr. Jenkins regarding Keytruda today, she was highly positive and requested trial details next week." I will decode the entities, save the interaction, and schedule tasks automatically!'
        }
      ]
    },
    addLocalUserMessage: (state, action) => {
      state.chatHistory.push({ role: 'user', content: action.payload })
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch HCPs
      .addCase(fetchHcps.pending, (state) => { state.status = 'loading' })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.hcps = action.payload
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })

      // Fetch HCP Details
      .addCase(fetchHcpDetails.fulfilled, (state, action) => {
        state.selectedHcp = action.payload
      })

      // Fetch Products
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.products = action.payload
      })

      // Fetch Interactions
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload
      })
      .addCase(addInteraction.fulfilled, (state, action) => {
        state.interactions.unshift(action.payload)
      })

      // Fetch Followups
      .addCase(fetchFollowups.fulfilled, (state, action) => {
        state.followups = action.payload
      })
      .addCase(toggleFollowup.fulfilled, (state, action) => {
        const updated = action.payload
        state.followups = state.followups.map(f => f.id === updated.id ? updated : f)
      })

      // Send Chat Message (LangGraph Integration)
      .addCase(sendChatMessage.pending, (state) => {
        state.chatLoading = true
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.chatLoading = false
        // Update history with the full chain sent by the backend
        state.chatHistory = action.payload.history
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.chatLoading = false
        state.chatHistory.push({
          role: 'assistant',
          content: `Error: ${action.error.message || 'Unable to connect to AI server. Please make sure the backend is active.'}`
        })
      })
  }
})

export const { clearChat, addLocalUserMessage } = crmSlice.actions
export default crmSlice.reducer
