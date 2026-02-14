import { useState, useEffect } from 'react'

function Controls({ voiceEnabled, onVoiceToggle, onSpeak }) {
  const [focusMode, setFocusMode] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(25 * 60) // 25 minutes in seconds
  const [timerActive, setTimerActive] = useState(false)
  
  // Focus timer countdown
  useEffect(() => {
    let interval = null
    
    if (timerActive && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(prev => prev - 1)
      }, 1000)
    } else if (timeRemaining === 0) {
      setTimerActive(false)
      // Alert user
      if ('speechSynthesis' in window && voiceEnabled) {
        const utterance = new SpeechSynthesisUtterance("Focus session complete! Great work!")
        window.speechSynthesis.speak(utterance)
      }
    }
    
    return () => clearInterval(interval)
  }, [timerActive, timeRemaining, voiceEnabled])
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  
  const toggleTimer = () => {
    if (timerActive) {
      setTimerActive(false)
    } else {
      setTimerActive(true)
      if (timeRemaining === 0) {
        setTimeRemaining(25 * 60)
      }
    }
  }
  
  const resetTimer = () => {
    setTimerActive(false)
    setTimeRemaining(25 * 60)
  }
  
  return (
    <>
      {/* Focus Timer (Innovation Feature) */}
      {focusMode && (
        <div className="focus-timer">
          <p className="timer-label">Focus Session</p>
          <div className="timer-display">
            {formatTime(timeRemaining)}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
            <button 
              className="btn btn-primary"
              onClick={toggleTimer}
              style={{ minWidth: '100px' }}
            >
              {timerActive ? '⏸️ Pause' : '▶️ Start'}
            </button>
            <button 
              className="btn"
              onClick={resetTimer}
              style={{ minWidth: '80px' }}
            >
              🔄 Reset
            </button>
          </div>
        </div>
      )}
      
      {/* Control buttons */}
      <div className="controls-bar">
        {/* Voice toggle */}
        <button 
          className={`btn btn-icon ${voiceEnabled ? 'active' : ''}`}
          onClick={onVoiceToggle}
          title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
          style={voiceEnabled ? { backgroundColor: 'var(--accent-success)' } : {}}
        >
          {voiceEnabled ? '🔊' : '🔇'}
        </button>
        
        {/* Read aloud button */}
        <button 
          className="btn btn-icon"
          onClick={onSpeak}
          title="Read current step"
        >
          🗣️
        </button>
        
        {/* Focus mode toggle */}
        <button 
          className={`btn btn-icon ${focusMode ? 'active' : ''}`}
          onClick={() => setFocusMode(!focusMode)}
          title="Focus timer"
          style={focusMode ? { backgroundColor: 'var(--accent-primary)' } : {}}
        >
          ⏱️
        </button>
      </div>
    </>
  )
}

export default Controls
