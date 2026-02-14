import { useState } from 'react'

function ProfileForm({ onSubmit, loading }) {
  const [name, setName] = useState('')
  const [fontPreference, setFontPreference] = useState('Lexend')
  const [highContrast, setHighContrast] = useState(false)
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim()) return
    
    onSubmit({
      name: name.trim(),
      font_preference: fontPreference,
      high_contrast: highContrast,
      triggers: [],
      preferences: {}
    })
  }
  
  return (
    <div className="card">
      <h2 className="card-header">Create Your Profile</h2>
      <p className="micro-text" style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
        Let's personalize your experience.
      </p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="name">
            What should I call you?
          </label>
          <input
            type="text"
            id="name"
            className="form-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            autoComplete="name"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">
            Choose your preferred font
          </label>
          <div className="toggle-container">
            <span style={{ fontFamily: 'Lexend' }}>Lexend</span>
            <div 
              className={`toggle-switch ${fontPreference === 'OpenDyslexic' ? 'active' : ''}`}
              onClick={() => setFontPreference(
                fontPreference === 'Lexend' ? 'OpenDyslexic' : 'Lexend'
              )}
            />
            <span style={{ fontFamily: 'OpenDyslexic' }}>OpenDyslexic</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            OpenDyslexic is designed to help with dyslexia
          </p>
        </div>
        
        <div className="form-group">
          <div className="toggle-container">
            <span>High Contrast Mode</span>
            <div 
              className={`toggle-switch ${highContrast ? 'active' : ''}`}
              onClick={() => setHighContrast(!highContrast)}
            />
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Black background with bright text
          </p>
        </div>
        
        <button 
          type="submit" 
          className="btn btn-primary btn-large"
          disabled={loading || !name.trim()}
        >
          {loading ? 'Creating...' : "Let's Get Started! 🚀"}
        </button>
      </form>
    </div>
  )
}

export default ProfileForm
