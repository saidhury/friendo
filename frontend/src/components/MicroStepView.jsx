function MicroStepView({ step, stepIndex, totalSteps, onComplete, loading }) {
  if (!step) {
    return (
      <div className="card">
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <p>No active task</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="micro-step-wrapper">
      <div className="card micro-step-container">
        {/* Step number badge */}
        <div className="step-number">
          {stepIndex + 1}
        </div>
        
        {/* Main action - large and clear */}
        <div className="step-action">
          {step.action}
        </div>
        
        {/* Estimated time */}
        <div className="step-time">
          ⏱️ About {step.estimated_minutes || 3} min
        </div>
      </div>
      
      {/* Fixed Complete button - always in same position */}
      <div className="complete-button-container">
        <button
          className="btn btn-success btn-large"
          onClick={onComplete}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ width: '20px', height: '20px', borderColor: 'white', borderTopColor: 'transparent' }}></span>
              Saving...
            </>
          ) : (
            <>
              ✅ Done! Mark Complete
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default MicroStepView
