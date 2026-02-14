function ProgressBar({ current, total }) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0
  
  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="progress-text">
        <span>{current} of {total} steps done</span>
        <span>{percentage}%</span>
      </div>
    </div>
  )
}

export default ProgressBar
