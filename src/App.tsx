import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import OSInterna from './pages/OSInterna'
import OSExterna from './pages/OSExterna'
import FiltrarOS from './pages/FiltrarOS'
import AtualizarOS from './pages/AtualizarOS'
import Home from './pages/Home'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/os-interna" element={<OSInterna />} />
        <Route path="/os-externa" element={<OSExterna />} />
        <Route path="/filtrar" element={<FiltrarOS />} />
        <Route path="/atualizar" element={<AtualizarOS />} />
      </Routes>
    </Layout>
  )
}

export default App