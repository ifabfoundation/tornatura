import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { AuthProvider } from './providers/auth-providers.tsx'
import { Provider } from 'react-redux'
import store from './store.ts'
import { AppRoutes } from './routes.tsx'
import { BrowserRouter } from 'react-router-dom'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <Provider store={store}>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </Provider>
    </AuthProvider>
  </StrictMode>,
)
