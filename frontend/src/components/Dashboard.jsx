import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHcps, fetchInteractions, fetchFollowups, toggleFollowup } from '../features/crmSlice'
import { Users, Calendar, Activity, CheckSquare, Plus, ExternalLink, CalendarRange } from 'lucide-react'

export default function Dashboard({ onViewHcp, onLogInteraction }) {
  const dispatch = useDispatch()
  const { hcps, interactions, followups, status } = useSelector((state) => state.crm)

  useEffect(() => {
    dispatch(fetchHcps())
    dispatch(fetchInteractions())
    dispatch(fetchFollowups())
  }, [dispatch])

  // Get active follow-ups count
  const pendingFollowups = followups.filter(f => !f.completed)
  
  const handleFollowupChange = (id) => {
    dispatch(toggleFollowup(id))
  }

  const getSentimentText = (score) => {
    if (score > 0.3) return { text: "Positive", emoji: "😊", class: "pos" }
    if (score < -0.1) return { text: "Negative", emoji: "😟", class: "neg" }
    return { text: "Neutral", emoji: "😐", class: "neu" }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ marginBottom: '6px' }}>HCP Executive Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Welcome back, Jane. Here is the overview of your relationships and clinical logs.</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={onLogInteraction}
        >
          <Plus size={16} />
          <span>Log New Interaction</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid-3">
        <div className="card kpi-card glow-card">
          <div className="kpi-icon" style={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' }}>
            <Users size={24} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Target HCPs</span>
            <span className="kpi-value">{hcps.length}</span>
          </div>
        </div>

        <div className="card kpi-card glow-card">
          <div className="kpi-icon" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
            <Activity size={24} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Logged Interactions</span>
            <span className="kpi-value">{interactions.length}</span>
          </div>
        </div>

        <div className="card kpi-card glow-card">
          <div className="kpi-icon" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
            <CalendarRange size={24} />
          </div>
          <div className="kpi-data">
            <span className="kpi-label">Pending Follow-ups</span>
            <span className="kpi-value">{pendingFollowups.length}</span>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* HCP Targets List */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Target Professionals</h2>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Region East</span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {hcps.map((hcp) => {
              const sentiment = getSentimentText(hcp.current_sentiment)
              const tierBadgeClass = hcp.tier.includes("1") ? "badge-tier1" : (hcp.tier.includes("2") ? "badge-tier2" : "badge-tier3")
              return (
                <div 
                  key={hcp.id} 
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    padding: '12px', 
                    borderRadius: 'var(--radius-sm)', 
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-color)'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: '600', fontSize: '14.5px', marginBottom: '2px' }}>
                      {hcp.name}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {hcp.specialty} • {hcp.hospital}
                    </div>
                    <div style={{ marginTop: '8px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span className={`badge ${tierBadgeClass}`}>{hcp.tier.split(' ')[0]}</span>
                      <span className={`badge badge-sentiment-${sentiment.class}`} style={{ textTransform: 'none' }}>
                        {sentiment.emoji} {sentiment.text}
                      </span>
                    </div>
                  </div>
                  <button 
                    className="btn btn-secondary" 
                    style={{ padding: '6px 12px', fontSize: '12px' }}
                    onClick={() => onViewHcp(hcp.id)}
                  >
                    View Timeline
                  </button>
                </div>
              )
            })}
          </div>
        </div>

        {/* Actionable Followups */}
        <div className="card">
          <h2>Pending Reminders Checklist</h2>
          {followups.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '24px' }}>
              All caught up! No scheduled follow-up reminders.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '320px', overflowY: 'auto' }}>
              {followups.map((task) => {
                const targetHcp = hcps.find(h => h.id === task.hcp_id)
                return (
                  <div 
                    key={task.id}
                    style={{ 
                      display: 'flex', 
                      gap: '12px', 
                      padding: '12px', 
                      borderRadius: 'var(--radius-sm)',
                      background: task.completed ? 'rgba(255, 255, 255, 0.01)' : 'rgba(255, 255, 255, 0.03)',
                      alignItems: 'center',
                      opacity: task.completed ? 0.6 : 1,
                      border: '1px solid var(--border-color)'
                    }}
                  >
                    <div 
                      className={`checkbox-custom ${task.completed ? 'checked' : ''}`}
                      onClick={() => handleFollowupChange(task.id)}
                    >
                      {task.completed && '✓'}
                    </div>

                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        fontSize: '13.5px', 
                        fontWeight: '500', 
                        textDecoration: task.completed ? 'line-through' : 'none',
                        color: task.completed ? 'var(--text-secondary)' : 'var(--text-primary)'
                      }}>
                        {task.task_description}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        For <strong>{targetHcp ? targetHcp.name : `HCP ID ${task.hcp_id}`}</strong> • Due: {task.due_date}
                      </div>
                    </div>
                    
                    <span 
                      className="badge" 
                      style={{ 
                        fontSize: '10px', 
                        padding: '2px 6px',
                        background: task.priority === 'High' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                        color: task.priority === 'High' ? '#f87171' : 'var(--text-secondary)'
                      }}
                    >
                      {task.priority}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Interactions Table Feed */}
      <div className="card" style={{ marginTop: '24px' }}>
        <h2 style={{ marginBottom: '20px' }}>Recent Meeting Audits</h2>
        {interactions.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '24px' }}>
            No interactions recorded yet. Complete the quick log to populate.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Physician</th>
                  <th>Date</th>
                  <th>Channels</th>
                  <th>Discussions</th>
                  <th>Outcome Assessment</th>
                  <th>AI Summary View</th>
                </tr>
              </thead>
              <tbody>
                {interactions.slice(0, 5).map((log) => {
                  const targetHcp = hcps.find(h => h.id === log.hcp_id)
                  const typeClass = log.interaction_type === 'In-Person' ? 'badge-type-inperson' : (log.interaction_type === 'Call' ? 'badge-type-call' : 'badge-type-email')
                  return (
                    <tr key={log.id}>
                      <td style={{ fontWeight: '500' }}>
                        {targetHcp ? targetHcp.name : `HCP ID ${log.hcp_id}`}
                      </td>
                      <td>{log.date}</td>
                      <td>
                        <span className={`badge ${typeClass}`}>{log.interaction_type}</span>
                      </td>
                      <td><strong>{log.products_discussed || 'N/A'}</strong></td>
                      <td>{log.outcome || 'N/A'}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '13px', maxPromptWidth: '250px' }}>
                        {log.ai_summary || log.notes}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
