import { useState, useEffect, useCallback } from 'react'
import ProfileForm from './components/ProfileForm'
import TaskInput from './components/TaskInput'
import MicroStepView from './components/MicroStepView'
import ProgressBar from './components/ProgressBar'
import Controls from './components/Controls'
import EnergyView from './components/EnergyView'
import VoiceCompanion from './components/VoiceCompanion'

// API base URL
const API_BASE = ''

function App() {
  // User state
  const [user, setUser] = useState(null)
  const [userId, setUserId] = useState(() => {
    return localStorage.getItem('smartCompanionUserId')
  })
  
  // UI state
  const [currentView, setCurrentView] = useState('home')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [celebration, setCelebration] = useState(null)
  const [showConfetti, setShowConfetti] = useState(false)
  
  // Task state
  const [activeTask, setActiveTask] = useState(null)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  
  // Voice state
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  
  // Load user on mount
  useEffect(() => {
    if (userId) {
      loadUser(userId)
    }
  }, [userId])
  
  // Apply user preferences
  useEffect(() => {
    if (user) {
      document.body.classList.toggle('high-contrast', user.high_contrast)
      document.body.classList.toggle('font-opendyslexic', user.font_preference === 'OpenDyslexic')
    }
  }, [user?.high_contrast, user?.font_preference])
  
  // API Functions
  const loadUser = async (id) => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/users/${id}`)
      if (res.ok) {
        const userData = await res.json()
        setUser(userData)
        // Check for active task
        await loadActiveTask(id)
      } else {
        // User not found, clear stored ID
        localStorage.removeItem('smartCompanionUserId')
        setUserId(null)
      }
    } catch (err) {
      console.error('Failed to load user:', err)
      setError('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }
  
  const createUser = async (userData) => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/users/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      })
      
      if (res.ok) {
        const newUser = await res.json()
        setUser(newUser)
        setUserId(newUser.id)
        localStorage.setItem('smartCompanionUserId', newUser.id)
        setCurrentView('home')
      } else {
        throw new Error('Failed to create profile')
      }
    } catch (err) {
      console.error('Create user error:', err)
      setError('Failed to create profile')
    } finally {
      setLoading(false)
    }
  }
  
  const updatePreferences = async (prefs) => {
    if (!user) return
    
    try {
      const res = await fetch(`${API_BASE}/users/${user.id}/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs)
      })
      
      if (res.ok) {
        const updatedUser = await res.json()
        setUser(updatedUser)
      }
    } catch (err) {
      console.error('Update preferences error:', err)
    }
  }
  
  const loadActiveTask = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/tasks/user/${id}/active`)
      if (res.ok) {
        const data = await res.json()
        if (data.active_task) {
          setActiveTask(data.active_task)
          setCurrentStepIndex(data.active_task.completed_steps)
          setCurrentView('task')
        }
      }
    } catch (err) {
      console.error('Failed to load active task:', err)
    }
  }
  
  const decomposeTask = async (goal) => {
    if (!user) return
    
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/tasks/decompose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          goal: goal
        })
      })
      
      if (res.ok) {
        const data = await res.json()
        setActiveTask({
          id: data.task_id,
          goal: data.goal,
          micro_steps: data.micro_steps,
          completed_steps: 0,
          total_steps: data.total_steps,
          complexity_score: data.complexity_score,
          suggested_energy_window: data.suggested_energy_window
        })
        setCurrentStepIndex(0)
        setCurrentView('task')
        
        // Speak first step if voice enabled
        if (voiceEnabled && data.micro_steps.length > 0) {
          speak("Let's start with this step: " + data.micro_steps[0].action)
        }
      } else {
        throw new Error('Failed to decompose task')
      }
    } catch (err) {
      console.error('Decompose error:', err)
      setError('Failed to break down task')
    } finally {
      setLoading(false)
    }
  }
  
  const completeStep = async () => {
    if (!activeTask || !user) return
    
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/tasks/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: activeTask.id,
          user_id: user.id
        })
      })
      
      if (res.ok) {
        const data = await res.json()
        
        // Show celebration
        setCelebration(data.celebration_message)
        setTimeout(() => setCelebration(null), 3000)
        
        // Update user streak
        setUser(prev => ({
          ...prev,
          streak_count: data.new_streak,
          badges: [...(prev.badges || []), ...data.badges_earned]
        }))
        
        if (data.is_fully_completed) {
          // Task complete!
          setShowConfetti(true)
          setTimeout(() => setShowConfetti(false), 3000)
          
          if (voiceEnabled) {
            speak(data.celebration_message)
          }
          
          // Reset task
          setActiveTask(null)
          setCurrentStepIndex(0)
          setCurrentView('home')
        } else {
          // Move to next step
          setCurrentStepIndex(data.completed_steps)
          setActiveTask(prev => ({
            ...prev,
            completed_steps: data.completed_steps
          }))
          
          // Speak next step
          const nextStep = activeTask.micro_steps[data.completed_steps]
          if (voiceEnabled && nextStep) {
            speak("Great! Next step: " + nextStep.action)
          }
        }
      }
    } catch (err) {
      console.error('Complete step error:', err)
      setError('Failed to complete step')
    } finally {
      setLoading(false)
    }
  }
  
  const logEnergy = async (level) => {
    if (!user) return
    
    try {
      await fetch(`${API_BASE}/energy/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          energy_level: level
        })
      })
    } catch (err) {
      console.error('Log energy error:', err)
    }
  }
  
  // Voice Functions
  const speak = useCallback((text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.9
      utterance.pitch = 1
      window.speechSynthesis.speak(utterance)
    }
  }, [])
  
  const toggleVoice = () => {
    setVoiceEnabled(prev => !prev)
    if (!voiceEnabled) {
      speak("Voice companion activated")
    }
  }
  
  // Toggle Functions
  const toggleHighContrast = () => {
    updatePreferences({ high_contrast: !user.high_contrast })
  }
  
  const toggleFont = () => {
    const newFont = user.font_preference === 'Lexend' ? 'OpenDyslexic' : 'Lexend'
    updatePreferences({ font_preference: newFont })
  }
  
  // Render Confetti
  const renderConfetti = () => {
    if (!showConfetti) return null
    
    const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6']
    const confetti = []
    
    for (let i = 0; i < 50; i++) {
      const style = {
        left: `${Math.random() * 100}%`,
        backgroundColor: colors[Math.floor(Math.random() * colors.length)],
        animationDelay: `${Math.random() * 2}s`,
        transform: `rotate(${Math.random() * 360}deg)`
      }
      confetti.push(<div key={i} className="confetti" style={style} />)
    }
    
    return <div className="confetti-container">{confetti}</div>
  }
  
  // Loading screen
  if (loading && !user && !activeTask) {
    return (
      <div className="app-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    )
  }
  
  // No user - show profile form
  if (!user) {
    return (
      <div className="app-container">
        <h1>🧠 Smart Companion</h1>
        <p style={{ textAlign: 'center', marginBottom: '2rem', color: 'var(--text-secondary)' }}>
          Your neuro-inclusive productivity partner
        </p>
        <ProfileForm onSubmit={createUser} loading={loading} />
      </div>
    )
  }
  
  // Current step for task view
  const currentStep = activeTask?.micro_steps?.[currentStepIndex]
  
  return (
    <div className="app-container">
      {renderConfetti()}
      
      {/* Header */}
      <header style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <h1>🧠 Smart Companion</h1>
        <div className="streak-display">
          <span className="streak-number">🔥 {user.streak_count}</span>
          <span className="streak-label">streak</span>
          <div className="badge-container">
            {user.badges?.map((badge, i) => (
              <span key={i} className="badge">
                {badge === 'bronze' && '🥉'}
                {badge === 'silver' && '🥈'}
                {badge === 'gold' && '🥇'}
                {badge === 'diamond' && '💎'}
              </span>
            ))}
          </div>
        </div>
      </header>
      
      {/* Navigation */}
      <nav className="nav-tabs">
        <button 
          className={`nav-tab ${currentView === 'home' ? 'active' : ''}`}
          onClick={() => setCurrentView('home')}
        >
          🏠 Home
        </button>
        <button 
          className={`nav-tab ${currentView === 'energy' ? 'active' : ''}`}
          onClick={() => setCurrentView('energy')}
        >
          ⚡ Energy
        </button>
        <button 
          className={`nav-tab ${currentView === 'settings' ? 'active' : ''}`}
          onClick={() => setCurrentView('settings')}
        >
          ⚙️ Settings
        </button>
      </nav>
      
      {/* Error Message */}
      {error && (
        <div className="message message-success" onClick={() => setError(null)}>
          {error} (tap to dismiss)
        </div>
      )}
      
      {/* Celebration Message */}
      {celebration && (
        <div className="message message-celebration">
          {celebration}
        </div>
      )}
      
      {/* Main Content */}
      {currentView === 'home' && !activeTask && (
        <div className="card">
          <h2 className="card-header">What would you like to do?</h2>
          <TaskInput onSubmit={decomposeTask} loading={loading} />
          <VoiceCompanion 
            enabled={voiceEnabled}
            onToggle={toggleVoice}
            onVoiceInput={decomposeTask}
          />
        </div>
      )}
      
      {currentView === 'home' && activeTask && currentStep && (
        <>
          <ProgressBar 
            current={activeTask.completed_steps}
            total={activeTask.total_steps}
          />
          
          {/* Cognitive Load Meter */}
          <div className="cognitive-load">
            <span className="cognitive-load-label">Complexity:</span>
            <div className="cognitive-load-bar">
              <div 
                className={`cognitive-load-fill ${
                  activeTask.complexity_score <= 3 ? 'low' : 
                  activeTask.complexity_score <= 6 ? 'medium' : 'high'
                }`}
                style={{ width: `${activeTask.complexity_score * 10}%` }}
              />
            </div>
            <span className="cognitive-load-label">
              {activeTask.complexity_score}/10
            </span>
          </div>
          
          <MicroStepView 
            step={currentStep}
            stepIndex={currentStepIndex}
            totalSteps={activeTask.total_steps}
            onComplete={completeStep}
            loading={loading}
          />
          
          <Controls
            voiceEnabled={voiceEnabled}
            onVoiceToggle={toggleVoice}
            onSpeak={() => speak(currentStep.action)}
          />
        </>
      )}
      
      {currentView === 'task' && activeTask && currentStep && (
        <>
          <ProgressBar 
            current={activeTask.completed_steps}
            total={activeTask.total_steps}
          />
          
          <MicroStepView 
            step={currentStep}
            stepIndex={currentStepIndex}
            totalSteps={activeTask.total_steps}
            onComplete={completeStep}
            loading={loading}
          />
          
          <Controls
            voiceEnabled={voiceEnabled}
            onVoiceToggle={toggleVoice}
            onSpeak={() => speak(currentStep.action)}
          />
        </>
      )}
      
      {currentView === 'energy' && (
        <EnergyView 
          userId={user.id}
          onLogEnergy={logEnergy}
        />
      )}
      
      {currentView === 'settings' && (
        <div className="card">
          <h2 className="card-header">Settings</h2>
          
          <div className="toggle-container">
            <span>High Contrast Mode</span>
            <div 
              className={`toggle-switch ${user.high_contrast ? 'active' : ''}`}
              onClick={toggleHighContrast}
            />
          </div>
          
          <div className="toggle-container">
            <span>OpenDyslexic Font</span>
            <div 
              className={`toggle-switch ${user.font_preference === 'OpenDyslexic' ? 'active' : ''}`}
              onClick={toggleFont}
            />
          </div>
          
          <div className="toggle-container">
            <span>Voice Companion</span>
            <div 
              className={`toggle-switch ${voiceEnabled ? 'active' : ''}`}
              onClick={toggleVoice}
            />
          </div>
          
          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Logged in as <strong>{user.name}</strong>
            </p>
            <button 
              className="btn"
              onClick={() => {
                localStorage.removeItem('smartCompanionUserId')
                setUser(null)
                setUserId(null)
                setActiveTask(null)
              }}
              style={{ marginTop: '1rem' }}
            >
              Switch Profile
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
