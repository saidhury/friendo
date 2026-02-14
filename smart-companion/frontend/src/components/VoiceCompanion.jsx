import { useState, useEffect, useCallback } from 'react'

function VoiceCompanion({ enabled, onToggle, onVoiceInput }) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [supported, setSupported] = useState(true)
  
  // Check for Web Speech API support
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setSupported(false)
    }
  }, [])
  
  const startListening = useCallback(() => {
    if (!supported) return
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'
    
    recognition.onstart = () => {
      setIsListening(true)
      setTranscript('')
    }
    
    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }
      
      setTranscript(finalTranscript || interimTranscript)
      
      if (finalTranscript) {
        onVoiceInput(finalTranscript)
      }
    }
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setIsListening(false)
    }
    
    recognition.onend = () => {
      setIsListening(false)
    }
    
    recognition.start()
  }, [supported, onVoiceInput])
  
  if (!supported) {
    return null
  }
  
  return (
    <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Or tell me what you want to do:
      </p>
      
      <button
        className={`voice-button ${isListening ? 'listening' : ''}`}
        onClick={startListening}
        disabled={isListening}
        style={{
          backgroundColor: isListening ? 'var(--accent-danger)' : 'var(--accent-primary)',
          color: 'white',
          margin: '0 auto'
        }}
      >
        {isListening ? '🎙️' : '🎤'}
      </button>
      
      {transcript && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          fontStyle: 'italic',
          color: 'var(--text-secondary)'
        }}>
          "{transcript}"
        </div>
      )}
      
      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
        {isListening ? 'Listening...' : 'Tap to speak'}
      </p>
    </div>
  )
}

export default VoiceCompanion
