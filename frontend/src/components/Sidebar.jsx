import React from 'react'
import { LayoutDashboard, MessageSquarePlus, User, Settings, ShieldAlert, Award } from 'lucide-react'

export default function Sidebar({ currentTab, setCurrentTab }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'log', label: 'Log Interaction', icon: MessageSquarePlus },
  ]

  return (
    <aside className="sidebar">
      <div className="logo">
        <Award className="icon-brand" size={24} style={{ color: 'var(--brand-color)' }} />
        <span style={{ letterSpacing: '-0.5px' }}>Aivoa CRM</span>
      </div>

      <nav style={{ flex: 1 }}>
        <ul className="nav-links">
          {menuItems.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.id}>
                <a
                  className={`nav-item ${currentTab === item.id ? 'active' : ''}`}
                  onClick={() => setCurrentTab(item.id)}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </a>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="user-badge" style={{ marginTop: 'auto', flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="user-avatar">JD</div>
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: '600' }}>Jane Doe</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Sales Representative</div>
          </div>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', width: '100%', paddingTop: '8px' }}>
          <strong>Territory:</strong> Boston Metro
        </div>
      </div>
    </aside>
  )
}
