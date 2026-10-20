import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import { ProvedorConfirmacao } from './components/Confirmacao'
import { AuthProvider } from './context/AuthContext'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ProvedorConfirmacao>
          <App />
        </ProvedorConfirmacao>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
