import { configureStore } from '@reduxjs/toolkit'
import crmReducer from '../features/crmSlice'

export const store = configureStore({
  reducer: {
    crm: crmReducer
  }
})
