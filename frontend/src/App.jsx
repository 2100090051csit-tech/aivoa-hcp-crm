import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import LogInteraction from './components/LogInteraction'
import HCPProfile from './components/HCPProfile'

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard') // dashboard, log, profile
  const [selectedHcpId, setSelectedHcpId] = useState(null)

  const handleViewHcp = (id) => {
    setSelectedHcpId(id)
    setCurrentTab('profile')
  }

  const handleLogInteraction = () => {
    setCurrentTab('log')
  }

  return (
    <div className="app-container">
      <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />
      
      <main className="main-content">
        {currentTab === 'dashboard' && (
          <Dashboard 
            onViewHcp={handleViewHcp} 
            onLogInteraction={handleLogInteraction} 
          />
        )}
        
        {currentTab === 'log' && (
          <LogInteraction 
            onNavigateBack={() => setCurrentTab('dashboard')} 
          />
        )}
        
        {currentTab === 'profile' && (
          <HCPProfile 
            hcpId={selectedHcpId} 
            onBack={() => setCurrentTab('dashboard')} 
          />
        )}
      </main>
    </div>
  )
}
