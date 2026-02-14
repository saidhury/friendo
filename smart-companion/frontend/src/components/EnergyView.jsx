import { useState, useEffect } from 'react'

function EnergyView({ userId, onLogEnergy }) {
  const [selectedEnergy, setSelectedEnergy] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [logged, setLogged] = useState(false)
  
  const energyLevels = [
    { level: 1, emoji: '😴', label: 'Very Low' },
    { level: 2, emoji: '😔', label: 'Low' },
    { level: 3, emoji: '😐', label: 'Medium' },
    { level: 4, emoji: '😊', label: 'Good' },
    { level: 5, emoji: '🔥', label: 'High' }
  ]
  
  // Load energy analysis
  useEffect(() => {
    loadAnalysis()
  }, [userId])
  
  const loadAnalysis = async () => {
    try {
      setLoading(true)
      const res = await fetch(`/energy/analysis/${userId}`)
      if (res.ok) {
        const data = await res.json()
        setAnalysis(data)
      }
    } catch (err) {
      console.error('Failed to load energy analysis:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const handleLogEnergy = async () => {
    if (selectedEnergy === null) return
    
    try {
      await onLogEnergy(selectedEnergy)
      setLogged(true)
      setTimeout(() => setLogged(false), 2000)
      // Refresh analysis
      loadAnalysis()
    } catch (err) {
      console.error('Failed to log energy:', err)
    }
  }
  
  const formatHour = (hour) => {
    if (hour === 0) return '12am'
    if (hour < 12) return `${hour}am`
    if (hour === 12) return '12pm'
    return `${hour - 12}pm`
  }
  
  return (
    <div>
      {/* Log Energy Card */}
      <div className="card">
        <h2 className="card-header">How's your energy right now?</h2>
        
        <div className="energy-meter">
          {energyLevels.map(({ level, emoji, label }) => (
            <button
              key={level}
              className={`energy-level ${selectedEnergy === level ? 'selected' : ''}`}
              onClick={() => setSelectedEnergy(level)}
              title={label}
            >
              {emoji}
            </button>
          ))}
        </div>
        
        {selectedEnergy && (
          <p className="energy-label">
            {energyLevels.find(e => e.level === selectedEnergy)?.label}
          </p>
        )}
        
        <button
          className="btn btn-primary"
          onClick={handleLogEnergy}
          disabled={selectedEnergy === null}
          style={{ width: '100%', marginTop: '1rem' }}
        >
          {logged ? '✅ Logged!' : 'Log Energy Level'}
        </button>
      </div>
      
      {/* Energy Analysis Card */}
      <div className="card">
        <h2 className="card-header">Your Energy Patterns</h2>
        
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        ) : analysis ? (
          <>
            {/* Current energy */}
            <div style={{ 
              textAlign: 'center', 
              padding: '1rem',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              marginBottom: '1rem'
            }}>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Right now ({formatHour(analysis.current_hour)})
              </p>
              <p style={{ fontSize: '1.5rem', fontWeight: '600' }}>
                {analysis.current_energy_label === 'high' && '🔥 High Energy'}
                {analysis.current_energy_label === 'medium' && '😊 Medium Energy'}
                {analysis.current_energy_label === 'low' && '😴 Low Energy'}
              </p>
            </div>
            
            {/* Peak hours */}
            {analysis.peak_hours?.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
                  🌟 Your Peak Hours
                </h3>
                <p style={{ color: 'var(--text-secondary)' }}>
                  {analysis.peak_hours.map(h => formatHour(h)).join(', ')}
                </p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Best for complex tasks
                </p>
              </div>
            )}
            
            {/* Low energy hours */}
            {analysis.low_energy_hours?.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
                  😌 Lower Energy Times
                </h3>
                <p style={{ color: 'var(--text-secondary)' }}>
                  {analysis.low_energy_hours.map(h => formatHour(h)).join(', ')}
                </p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Good for simple tasks
                </p>
              </div>
            )}
            
            {/* Tip */}
            <div style={{
              padding: '1rem',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              borderRadius: 'var(--radius-md)',
              borderLeft: '3px solid var(--accent-primary)'
            }}>
              <p style={{ fontSize: '0.9rem' }}>
                💡 <strong>Tip:</strong> Log your energy regularly to get better recommendations!
              </p>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <p>Log your energy a few times to see patterns!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default EnergyView
