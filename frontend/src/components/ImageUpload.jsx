import { useState, useRef } from 'react'

function ImageUpload({ imagePrompt, onSubmit, onSkip }) {
  const [preview, setPreview] = useState(null)
  const [imageData, setImageData] = useState(null)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef(null)
  
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    setLoading(true)
    try {
      const previewUrl = URL.createObjectURL(file)
      setPreview(previewUrl)
      
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result.split(',')[1])
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      
      setImageData({ base64, mimeType: file.type || 'image/jpeg' })
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmit = () => {
    if (imageData) onSubmit(imageData)
  }
  
  const handleClear = () => {
    setPreview(null)
    setImageData(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }
  
  return (
    <div className="image-upload-overlay">
      <div className="image-upload-modal card">
        {imagePrompt && (
          <p className="image-upload-prompt">{imagePrompt}</p>
        )}
        
        {!preview ? (
          <div className="image-upload-actions">
            <label className="btn btn-primary btn-large image-upload-btn">
              <span>📷 Add Photo</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </label>
            
            <button 
              type="button"
              className="btn btn-large"
              onClick={onSkip}
            >
              Skip
            </button>
          </div>
        ) : (
          <div className="image-preview-container">
            <img src={preview} alt="Preview" className="image-preview" />
            <div className="image-upload-actions">
              <button 
                type="button"
                className="btn btn-primary btn-large"
                onClick={handleSubmit}
                disabled={loading}
              >
                ✓ Use Photo
              </button>
              <button 
                type="button"
                className="btn btn-large"
                onClick={handleClear}
                disabled={loading}
              >
                ✕ Remove
              </button>
            </div>
          </div>
        )}
        
        {loading && <div className="image-upload-loading">Processing...</div>}
      </div>
    </div>
  )
}

export default ImageUpload
