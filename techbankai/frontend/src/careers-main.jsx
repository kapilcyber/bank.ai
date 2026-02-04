import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import Careers from './pages/Careers'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

// Check if root element exists
const rootElement = document.getElementById('careers-root')
if (!rootElement) {
  throw new Error('Root element not found! Check careers.html for <div id="careers-root"></div>')
}

console.log('🚀 Starting Careers app on port 3005...')
console.log('Root element:', rootElement)

try {
  const root = ReactDOM.createRoot(rootElement)
  console.log('✅ React root created')

  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <Careers />
        </BrowserRouter>
      </ErrorBoundary>
    </React.StrictMode>,
  )
  console.log('✅ Careers app rendered')
} catch (error) {
  console.error('❌ Failed to render Careers app:', error)
  rootElement.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial; background: white; min-height: 100vh;">
      <h1>Failed to load careers page</h1>
      <p><strong>Error:</strong> ${error.message}</p>
      <p><strong>Stack:</strong></p>
      <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">${error.stack}</pre>
      <p>Check the browser console (F12) for more details.</p>
    </div>
  `
}

