import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { AuthProvider } from './providers/auth-providers.tsx'
import { Provider } from 'react-redux'
import store from './store.ts'
import { AppRoutes } from './routes.tsx'
import { BrowserRouter } from 'react-router-dom'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'mapbox-gl/dist/mapbox-gl.css';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import './index.css'
import { CurrentPositionProvider } from './providers/gps-providers.tsx'
import ReactGA from "react-ga4";

ReactGA.initialize("G-214S65X76W");

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <CurrentPositionProvider>
        <Provider store={store}>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </Provider>
      </CurrentPositionProvider>
    </AuthProvider>
  </StrictMode>,
)
