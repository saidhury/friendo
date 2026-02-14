import { useState } from 'react'

function TaskInput({ onSubmit, loading }) {
  const [goal, setGoal] = useState('')
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!goal.trim() || loading) return
    
    onSubmit(goal.trim())
    setGoal('')
  }
  
  const exampleGoals = [
    "Clean my room",
    "Write an email",
    "Start exercising",
    "Study for exam",
    "Organize my desk"
  ]
  
  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="goal">
          What's your goal?
        </label>
        <textarea
          id="goal"
          className="form-textarea"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Example: Clean my room"
          rows={3}
          style={{ minHeight: '80px' }}
        />
      </div>
      
      {/* Quick examples */}
      <div style={{ marginBottom: '1rem' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Try one of these:
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {exampleGoals.map((example, i) => (
            <button
              key={i}
              type="button"
              className="btn"
              style={{ 
                minWidth: 'auto', 
                padding: '0.5rem 0.75rem',
                fontSize: '0.85rem',
                backgroundColor: 'var(--bg-secondary)'
              }}
              onClick={() => setGoal(example)}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
      
      <button 
        type="submit" 
        className="btn btn-primary btn-large"
        disabled={loading || !goal.trim()}
      >
        {loading ? (
          <>
            <span className="spinner" style={{ width: '20px', height: '20px' }}></span>
            Breaking it down...
          </>
        ) : (
          "Break It Down ✨"
        )}
      </button>
    </form>
  )
}

export default TaskInput
