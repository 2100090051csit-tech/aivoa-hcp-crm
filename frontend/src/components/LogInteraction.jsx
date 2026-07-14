import React, { useState, useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { 
  addInteraction, 
  sendChatMessage, 
  clearChat, 
  addLocalUserMessage,
  fetchHcps, 
  fetchInteractions, 
  fetchFollowups 
} from '../features/crmSlice'
import { Send, Sparkles, FormInput, AlertCircle, CheckCircle, Database, HelpCircle, FileText, Ban } from 'lucide-react'

export default function LogInteraction({ onNavigateBack }) {
  const dispatch = useDispatch()
  const chatBottomRef = useRef(null)
  
  const { hcps, chatHistory, chatLoading } = useSelector((state) => state.crm)
  
  // Form States
  const [formData, setFormData] = useState({
    hcp_id: '',
    interaction_type: 'In-Person',
    date: new Date().toISOString().split('T')[0],
    notes: '',
    sentiment: 'Positive',
    products_discussed: '',
    outcome: '',
    next_steps: '',
    brochures_shared: false,
    user_id: 1 // Default rep profile
  })
  
  // Notification states
  const [notification, setNotification] = useState(null)
  
  // Chat Prompt State
  const [chatInput, setChatInput] = useState('')

  useEffect(() => {
    dispatch(fetchHcps())
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [dispatch, chatHistory])

  const handleFormChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFormSubmit = (e) => {
    e.preventDefault()
    if (!formData.hcp_id) {
      setNotification({ type: 'error', message: 'Please select an HCP Physician or let the AI resolve it.' })
      return
    }
    
    // Format note for SQL inclusion
    const submissionData = {
      ...formData,
      outcome: formData.brochures_shared 
        ? `${formData.outcome || ''} (Brochures shared)`.trim() 
        : formData.outcome
    }
    
    dispatch(addInteraction(submissionData))
      .unwrap()
      .then(() => {
        setNotification({ type: 'success', message: 'Interaction successfully verified and logged!' })
        // Reset Form
        setFormData({
          hcp_id: '',
          interaction_type: 'In-Person',
          date: new Date().toISOString().split('T')[0],
          notes: '',
          sentiment: 'Positive',
          products_discussed: '',
          outcome: '',
          next_steps: '',
          brochures_shared: false,
          user_id: 1
        })
        
        // Sync Lists
        dispatch(fetchInteractions())
        dispatch(fetchFollowups())
        
        setTimeout(() => {
          setNotification(null)
          onNavigateBack() // return to dashboard
        }, 2000)
      })
      .catch((err) => {
        setNotification({ type: 'error', message: err.message || 'Submit failed' })
      })
  }

  const handleChatSend = (e) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const messageToSend = chatInput
    setChatInput('')

    // Append message user side locally
    dispatch(addLocalUserMessage(messageToSend))

    // Call LangGraph on server
    dispatch(sendChatMessage({ 
      message: messageToSend, 
      history: chatHistory 
    }))
      .unwrap()
      .then((res) => {
        // Resolve tool calls to pre-fill the form on the left in real-time!
        const toolCalls = res.state_updates?.tool_calls || [];
        toolCalls.forEach(tc => {
          if (tc.name === 'log_interaction') {
            const noteText = tc.args.notes ? tc.args.notes.toLowerCase() : '';
            const outcomeText = tc.args.outcome ? tc.args.outcome.toLowerCase() : '';
            const brochuresShared = noteText.includes('brochure') || outcomeText.includes('brochure') || tc.args.brochures_shared === true;
            
            setFormData(prev => ({
              ...prev,
              hcp_id: tc.args.hcp_id || prev.hcp_id,
              interaction_type: tc.args.interaction_type || prev.interaction_type,
              date: tc.args.date_str || tc.args.date || prev.date,
              notes: tc.args.notes || prev.notes,
              sentiment: tc.args.sentiment || prev.sentiment,
              products_discussed: tc.args.products_discussed || prev.products_discussed,
              outcome: tc.args.outcome || prev.outcome,
              next_steps: tc.args.next_steps || prev.next_steps,
              brochures_shared: brochuresShared
            }));
          } else if (tc.name === 'edit_interaction') {
            setFormData(prev => {
              const noteText = tc.args.notes ? tc.args.notes.toLowerCase() : '';
              const outcomeText = tc.args.outcome ? tc.args.outcome.toLowerCase() : '';
              const updatedBrochures = tc.args.brochures_shared !== undefined ? tc.args.brochures_shared :
                (tc.args.notes || tc.args.outcome ? (noteText.includes('brochure') || outcomeText.includes('brochure')) : prev.brochures_shared);
              
              return {
                ...prev,
                hcp_id: tc.args.hcp_id !== undefined ? tc.args.hcp_id : prev.hcp_id,
                interaction_type: tc.args.interaction_type !== undefined ? tc.args.interaction_type : prev.interaction_type,
                date: (tc.args.date_str || tc.args.date) !== undefined ? (tc.args.date_str || tc.args.date) : prev.date,
                notes: tc.args.notes !== undefined ? tc.args.notes : prev.notes,
                sentiment: tc.args.sentiment !== undefined ? tc.args.sentiment : prev.sentiment,
                products_discussed: tc.args.products_discussed !== undefined ? tc.args.products_discussed : prev.products_discussed,
                outcome: tc.args.outcome !== undefined ? tc.args.outcome : prev.outcome,
                next_steps: tc.args.next_steps !== undefined ? tc.args.next_steps : prev.next_steps,
                brochures_shared: updatedBrochures
              };
            });
          }
        });

        // Sync lists if DB was mutated
        if (res.state_updates && res.state_updates.db_mutated) {
          setNotification({ 
            type: 'ai', 
            message: 'AI Tool Triggered: Interaction written and synced automatically in CRM database!' 
          })
          dispatch(fetchHcps())
          dispatch(fetchInteractions())
          dispatch(fetchFollowups())
          
          setTimeout(() => setNotification(null), 4000)
        }
      })
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ marginBottom: '6px' }}>Log HCP Interaction</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Real-time split screen layout. Control the form by chatting with the AI Assistant on the right.
        </p>
      </div>

      {notification && (
        <div style={{
          padding: '16px',
          borderRadius: 'var(--radius-sm)',
          background: notification.type === 'success' ? 'var(--success-glow)' : 
                     (notification.type === 'ai' ? 'var(--brand-glow)' : 'rgba(239, 68, 68, 0.1)'),
          border: `1px solid ${notification.type === 'success' ? 'var(--success)' : 
                               (notification.type === 'ai' ? 'var(--brand-color)' : 'var(--error)')}`,
          color: notification.type === 'success' ? 'var(--success)' : 
                 (notification.type === 'ai' ? '#c7d2fe' : 'var(--error)'),
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          {notification.type === 'success' && <CheckCircle size={20} />}
          {notification.type === 'error' && <AlertCircle size={20} />}
          {notification.type === 'ai' && <Database size={20} style={{ color: 'var(--brand-color)' }} />}
          <span style={{ fontSize: '14px', fontWeight: '500' }}>{notification.message}</span>
        </div>
      )}

      {/* Split Screen Container */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '24px', alignItems: 'stretch' }}>
        
        {/* Left Side: Interaction Details Panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            marginBottom: '20px', 
            borderBottom: '1px solid var(--border-color)', 
            paddingBottom: '12px' 
          }}>
            <h2 style={{ fontSize: '18px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} style={{ color: 'var(--brand-color)' }} />
              Interaction Details
            </h2>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: 'var(--brand-glow)', 
              color: 'var(--brand-color)', 
              padding: '4px 10px', 
              borderRadius: '20px', 
              fontSize: '11px', 
              fontWeight: 'bold',
              border: '1px solid rgba(99, 102, 241, 0.2)'
            }}>
              <Sparkles size={12} />
              <span>AI Controlled Form</span>
            </div>
          </div>

          <form onSubmit={handleFormSubmit} style={{ flexGrow: 1 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Select Healthcare Professional *</label>
                <select 
                  className="form-control" 
                  name="hcp_id" 
                  value={formData.hcp_id}
                  onChange={handleFormChange}
                  required
                  style={{ fontSize: '13px' }}
                >
                  <option value="">-- Choose HCP Physician --</option>
                  {hcps.map(h => (
                    <option key={h.id} value={h.id}>{h.name} ({h.specialty} - {h.hospital})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Interaction Channel Type *</label>
                <select 
                  className="form-control" 
                  name="interaction_type" 
                  value={formData.interaction_type}
                  onChange={handleFormChange}
                  style={{ fontSize: '13px' }}
                >
                  <option value="In-Person">In-Person Visit</option>
                  <option value="Call">Phone Call</option>
                  <option value="Email">Email Communication</option>
                  <option value="Video">Video Conference</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '16px' }}>
              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Meeting Date</label>
                <input 
                  type="date" 
                  className="form-control" 
                  name="date"
                  value={formData.date}
                  onChange={handleFormChange}
                  style={{ fontSize: '13px' }}
                />
              </div>

              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Products Discussed</label>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="e.g. Keytruda, Entresto"
                  name="products_discussed"
                  value={formData.products_discussed}
                  onChange={handleFormChange}
                  style={{ fontSize: '13px' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px', gap: '16px', alignItems: 'center' }}>
              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Doctor Sentiment Rating</label>
                <select 
                  className="form-control" 
                  name="sentiment" 
                  value={formData.sentiment}
                  onChange={handleFormChange}
                  style={{ fontSize: '13px' }}
                >
                  <option value="Positive">Positive Interest - High Potential</option>
                  <option value="Neutral">Neutral - Average Interest</option>
                  <option value="Negative">Negative / Hard Pushback</option>
                </select>
              </div>

              {/* Brochures Shared Checkbox visual element */}
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
                <input 
                  type="checkbox" 
                  id="brochures_shared"
                  name="brochures_shared"
                  checked={formData.brochures_shared}
                  onChange={(e) => setFormData(prev => ({ ...prev, brochures_shared: e.target.checked }))}
                  style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--brand-color)' }}
                />
                <label htmlFor="brochures_shared" style={{ cursor: 'pointer', margin: 0, fontSize: '13px', fontWeight: '500', userSelect: 'none' }}>
                  Brochures Shared
                </label>
              </div>
            </div>

            <div className="form-group">
              <label style={{ fontSize: '12px' }}>Interaction Notes *</label>
              <textarea 
                className="form-control" 
                placeholder="Detail the discussion points, physician queries, clinical data presented..."
                name="notes"
                value={formData.notes}
                onChange={handleFormChange}
                required
                style={{ height: '70px', fontSize: '13px' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Outcome Assessment</label>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="Summarize outcome..."
                  name="outcome"
                  value={formData.outcome}
                  onChange={handleFormChange}
                  style={{ fontSize: '13px' }}
                />
              </div>

              <div className="form-group">
                <label style={{ fontSize: '12px' }}>Next Steps / Pending Task</label>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="Future actions..."
                  name="next_steps"
                  value={formData.next_steps}
                  onChange={handleFormChange}
                  style={{ fontSize: '13px' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
              <button type="submit" className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '13px' }}>
                Verify & Save Interaction
              </button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setFormData({
                  hcp_id: '',
                  interaction_type: 'In-Person',
                  date: new Date().toISOString().split('T')[0],
                  notes: '',
                  sentiment: 'Positive',
                  products_discussed: '',
                  outcome: '',
                  next_steps: '',
                  brochures_shared: false,
                  user_id: 1
                })}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                Reset UI Form
              </button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={onNavigateBack}
                style={{ padding: '8px 16px', fontSize: '13px', marginLeft: 'auto' }}
              >
                Back
              </button>
            </div>
          </form>
        </div>

        {/* Right Side: AI Assistant Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Chat Interface Panel */}
          <div className="card" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', minHeight: '380px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              marginBottom: '14px', 
              borderBottom: '1px solid var(--border-color)', 
              paddingBottom: '10px' 
            }}>
              <h2 style={{ fontSize: '16px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} style={{ color: 'var(--brand-color)' }} />
                AI Assistant Chat
              </h2>
              <button 
                type="button"
                onClick={() => dispatch(clearChat())}
                style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}
              >
                Clear Chat History
              </button>
            </div>

            <div className="chat-window" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '280px' }}>
              <div className="chat-messages" style={{ flexGrow: 1, overflowY: 'auto', padding: '12px' }}>
                {chatHistory.map((msg, index) => (
                  <div 
                    key={index} 
                    className={`chat-bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}
                    style={{ fontSize: '13px', margin: '6px 0', padding: '8px 12px', borderRadius: '8px' }}
                  >
                    <div dangerouslySetInnerHTML={{ 
                      __html: msg.content
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/- (.*?)\n/g, '• $1<br/>')
                        .replace(/\n/g, '<br/>')
                    }} />
                  </div>
                ))}
                
                {chatLoading && (
                  <div className="chat-bubble bubble-assistant chat-loader" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Sparkles size={12} style={{ color: 'var(--brand-color)', animation: 'spin 2s linear infinite' }} />
                    <span>Orchestrating LangGraph tools...</span>
                  </div>
                )}
                
                <div ref={chatBottomRef} />
              </div>

              <form onSubmit={handleChatSend} className="chat-input-area" style={{ display: 'flex', borderTop: '1px solid var(--border-color)', background: 'transparent' }}>
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="Ask the AI to populate the form (e.g. 'Today I met with Dr. Smith...')"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={chatLoading}
                  style={{ border: 'none', background: 'transparent', borderRadius: '0', flexGrow: 1, padding: '12px', fontSize: '13px' }}
                />
                
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={chatLoading}
                  style={{ 
                    borderTopLeftRadius: '0', 
                    borderBottomLeftRadius: '0', 
                    padding: '0 18px',
                    fontSize: '13px',
                    fontWeight: '600'
                  }}
                >
                  Log
                </button>
              </form>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
