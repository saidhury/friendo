import { useState, useEffect } from 'react'

function ProfileForm({ onSubmit, loading }) {
  const [name, setName] = useState('')
  const [fontPreference, setFontPreference] = useState('Lexend')
  const [highContrast, setHighContrast] = useState(false)
  
  // Apply preview styles when toggling preferences
  useEffect(() => {
    document.body.classList.toggle('high-contrast', highContrast)
    return () => {
      // Cleanup on unmount (in case user doesn't submit)
      document.body.classList.remove('high-contrast')
    }
  }, [highContrast])
  
  useEffect(() => {
    document.body.classList.toggle('font-opendyslexic', fontPreference === 'OpenDyslexic')
    return () => {
      document.body.classList.remove('font-opendyslexic')
    }
  }, [fontPreference])
  
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
  
  const toggleFont = () => {
    setFontPreference(prev => prev === 'Lexend' ? 'OpenDyslexic' : 'Lexend')
  }
  
  const toggleContrast = () => {
    setHighContrast(prev => !prev)
  }
  
  return (
    <div className="card">
      <h2 className="card-header">Create Your Profile</h2>
      
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
            Choose your preferred settings
          </label>
          <div className="toggle-container">
            <span style={{ fontFamily: 'Lexend' }}>Lexend</span>
            <button
              type="button"
              className={`toggle-switch ${fontPreference === 'OpenDyslexic' ? 'active' : ''}`}
              onClick={toggleFont}
              aria-pressed={fontPreference === 'OpenDyslexic'}
              aria-label="Toggle font between Lexend and OpenDyslexic"
            />
            <span style={{ fontFamily: 'OpenDyslexic' }}>OpenDyslexic</span>
          </div>
        </div>
        
        <div className="form-group">
          <div className="toggle-container">
            <span>High Contrast Mode</span>
            <button
              type="button"
              className={`toggle-switch ${highContrast ? 'active' : ''}`}
              onClick={toggleContrast}
              aria-pressed={highContrast}
              aria-label="Toggle high contrast mode"
            />
          </div>
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
