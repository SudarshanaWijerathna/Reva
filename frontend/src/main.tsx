import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'

// Import your custom styles
import './assets/css/style.css'
// Import Leaflet CSS
import 'leaflet/dist/leaflet.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)