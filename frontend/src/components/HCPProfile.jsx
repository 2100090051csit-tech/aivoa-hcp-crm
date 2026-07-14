import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHcpDetails, fetchInteractions, fetchFollowups, toggleFollowup } from '../features/crmSlice'
import { User, Shield, Briefcase, Phone, Mail, Award, Calendar, ChevronRight, Activity, ArrowLeft } from 'lucide-react'

export default function HCPProfile({ hcpId, onBack }) {
  const dispatch = useDispatch()
  const { selectedHcp, interactions, followups } = useSelector((state) => state.crm)
  const [selectedLog, setSelectedLog] = useState(null)

  useEffect(() => {
    dispatch(fetchHcpDetails(hcpId))
    dispatch(fetchInteractions())
    dispatch(fetchFollowups())
  }, [dispatch, hcpId])

  if (!selectedHcp) {
    return (
      <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh' }}>
        Loading HCP dossier...
      </div>
    )
  }

  // Filter logs for this HCP
  const hcpInteractions = interactions.filter(i => i.hcp_id === hcpId)
  
  // Filter followups for this HCP
  const hcpFollowups = followups.filter(f => f.hcp_id === hcpId)

  // Sentiment history extraction
  // Let's create an array of sentiment scores over time (latest first) to visualize
  const sentimentHist = hcpInteractions.map(i => {
    if (i.sentiment === 'Positive') return 1.0
    if (i.sentiment === 'Negative') return -1.0
    return 0.0
  })

  // Simple completion handler
  const handleFollowupChange = (id) => {
    dispatch(toggleFollowup(id))
  }

  const getSentimentText = (score) => {
    if (score > 0.3) return { text: "Positive Focus", emoji: "😊", class: "pos", color: "#10b981" }
    if (score < -0.1) return { text: "Critical Focus", emoji: "😟", class: "neg", color: "#ef4444" }
    return { text: "Steady/Neutral", emoji: "😐", class: "neu", color: "#f59e0b" }
  }

  const overallSentiment = getSentimentText(selectedHcp.current_sentiment)

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <button 
          className="btn btn-secondary" 
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 16px', fontSize: '13px' }}
        >
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Left Dossier Details Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card">
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <div 
                style={{ 
                  width: '80px', 
                  height: '80px', 
                  borderRadius: '50%', 
                  background: 'var(--gradient-main)',
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  fontSize: '28px',
                  fontWeight: 'bold',
                  color: 'white',
                  margin: '0 auto 16px'
                }}
              >
                {selectedHcp.name.split(' ').slice(-1)[0][0]}
              </div>
              <h2 style={{ fontSize: '22px', marginBottom: '4px' }}>{selectedHcp.name}</h2>
              <span className="badge badge-tier1" style={{ fontSize: '12px' }}>{selectedHcp.tier}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Briefcase size={16} style={{ color: 'var(--text-secondary)' }} />
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Specialty / Subspecialty</div>
                  <div style={{ fontSize: '13.5px', fontWeight: '500' }}>{selectedHcp.specialty}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Award size={16} style={{ color: 'var(--text-secondary)' }} />
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Primary Affiliation</div>
                  <div style={{ fontSize: '13.5px', fontWeight: '500' }}>{selectedHcp.hospital}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Shield size={16} style={{ color: 'var(--text-secondary)' }} />
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>NPI Registry Number</div>
                  <div style={{ fontSize: '13.5px', fontWeight: '500' }}>{selectedHcp.npi}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Phone size={16} style={{ color: 'var(--text-secondary)' }} />
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Office Direct Line</div>
                  <div style={{ fontSize: '13.5px', fontWeight: '500' }}>{selectedHcp.phone || 'Not available'}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Mail size={16} style={{ color: 'var(--text-secondary)' }} />
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Email Address</div>
                  <div style={{ fontSize: '13.5px', fontWeight: '500', color: 'var(--brand-color)' }}>{selectedHcp.email || 'Not available'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Sentiment Widget with SVG Trend line graph */}
          <div className="card">
            <h2>Sentiment Score Tracker</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <span style={{ fontSize: '32px' }}>{overallSentiment.emoji}</span>
              <div>
                <span style={{ fontSize: '16px', fontWeight: '600', color: overallSentiment.color }}>{overallSentiment.text}</span>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>Current Average: {selectedHcp.current_sentiment.toFixed(2)}</div>
              </div>
            </div>

            {/* Custom SVG Trend Graph (highly robust, no dep errors) */}
            <div style={{ width: '100%', height: '100px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', padding: '10px 4px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, position: 'relative' }}>
                {sentimentHist.length < 2 ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px', textAlign: 'center', marginTop: '24px' }}>
                    Need +2 sessions logged to graph trend.
                  </div>
                ) : (
                  <svg width="100%" height="100%" viewBox="0 0 100 30" preserveAspectRatio="none">
                    {/* Grid lines */}
                    <line x1="0" y1="15" x2="100" y2="15" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
                    {/* Path line connecting weights */}
                    <path
                      d={`M ${sentimentHist.map((val, idx) => {
                        const x = (idx / (sentimentHist.length - 1)) * 100
                        const y = 15 - (val * 12) // positive goes up (negative y in svg)
                        return `${x} ${y}`
                      }).join(' L ')}`}
                      fill="none"
                      stroke="var(--brand-color)"
                      strokeWidth="2.5"
                    />
                    {/* Data dots */}
                    {sentimentHist.map((val, idx) => {
                      const x = (idx / (sentimentHist.length - 1)) * 100
                      const y = 15 - (val * 12)
                      return (
                        <circle 
                          key={idx} 
                          cx={x} 
                          cy={y} 
                          r="2" 
                          fill={val > 0.1 ? '#10b981' : (val < -0.1 ? '#ef4444' : '#f59e0b')} 
                        />
                      )
                    })}
                  </svg>
                )}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                <span>Past</span>
                <span>Current Visit</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Interactions & Tasks Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Follow-ups */}
          <div className="card">
            <h2>Pending Action Reminders</h2>
            {hcpFollowups.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '12px' }}>
                No scheduled followups for {selectedHcp.name}.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {hcpFollowups.map(t => (
                  <div 
                    key={t.id} 
                    style={{ 
                      display: 'flex', 
                      gap: '12px', 
                      alignItems: 'center',
                      background: 'rgba(255,255,255,0.01)',
                      border: '1px solid var(--border-color)',
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)'
                    }}
                  >
                    <div 
                      className={`checkbox-custom ${t.completed ? 'checked' : ''}`}
                      onClick={() => handleFollowupChange(t.id)}
                    >
                      {t.completed && '✓'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13.5px', fontWeight: '500', textDecoration: t.completed ? 'line-through' : 'none' }}>
                        {t.task_description}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        Due Date: {t.due_date} • Priority: {t.priority}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Interaction Timeline List */}
          <div className="card">
            <h2>Engagement History</h2>
            {hcpInteractions.length === 0 ? (
              <div style={{ padding: '24px', color: 'var(--text-muted)', textAlign: 'center' }}>
                No meetings or correspondence registered yet.
              </div>
            ) : (
              <div className="timeline">
                {hcpInteractions.map((log) => {
                  const isPos = log.sentiment === 'Positive'
                  const isNeg = log.sentiment === 'Negative'
                  const color = isPos ? 'var(--success)' : (isNeg ? 'var(--error)' : 'var(--warning)')
                  const typeClass = log.interaction_type === 'In-Person' ? 'badge-type-inperson' : (log.interaction_type === 'Call' ? 'badge-type-call' : 'badge-type-email')
                  
                  return (
                    <div className="timeline-item" key={log.id}>
                      <span className="timeline-dot" style={{ backgroundColor: color }} />
                      <div 
                        style={{ 
                          padding: '16px', 
                          background: selectedLog?.id === log.id ? 'var(--bg-hover)' : 'rgba(255, 255, 255, 0.02)',
                          border: '1px solid var(--border-color)',
                          borderRadius: 'var(--radius-sm)',
                          cursor: 'pointer',
                          marginLeft: '8px'
                        }}
                        onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span className={`badge ${typeClass}`}>{log.interaction_type}</span>
                            <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>{log.date}</span>
                          </div>
                          <span style={{ fontSize: '11px', color: isPos ? '#34d399' : (isNeg ? '#f87171' : '#fbbf24') }}>
                            {log.sentiment} Rating
                          </span>
                        </div>
                        
                        <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>
                          Product discussed: <span style={{ color: 'var(--brand-color)' }}>{log.products_discussed || 'None'}</span>
                        </div>
                        
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                          {log.ai_summary || log.notes.substring(0, 100) + '...'}
                        </p>
                        
                        {selectedLog?.id === log.id && (
                          <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-color)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            <div>
                              <strong style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Detailed notes</strong>
                              <p style={{ fontSize: '13px', marginTop: '4px', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{log.notes}</p>
                            </div>
                            
                            {log.outcome && (
                              <div>
                                <strong style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Notes Outcome Assessment</strong>
                                <p style={{ fontSize: '13px', marginTop: '4px' }}>{log.outcome}</p>
                              </div>
                            )}

                            {log.next_steps && (
                              <div>
                                <strong style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Required Next Steps</strong>
                                <p style={{ fontSize: '13px', marginTop: '4px', color: '#a78bfa' }}>{log.next_steps}</p>
                              </div>
                            )}
                          </div>
                        )}
                        
                        <div style={{ display: 'flex', justifyContent: 'flex-end', fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>
                          {selectedLog?.id === log.id ? 'Click card to collapse details' : 'Click card to expand details'}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
