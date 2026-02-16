#!/bin/bash
# Smart Companion - Quick Setup Script (Linux/Mac)
# Run: chmod +x setup.sh && ./setup.sh

echo "🚀 Smart Companion - Quick Setup"
echo "================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    # Generate encryption key
    echo "🔐 Generating encryption key..."
    KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null)
    
    if [ -n "$KEY" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^ENCRYPTION_KEY=.*$/ENCRYPTION_KEY=$KEY/" .env
        else
            sed -i "s/^ENCRYPTION_KEY=.*$/ENCRYPTION_KEY=$KEY/" .env
        fi
        echo "✅ Encryption key generated!"
    else
        echo "⚠️  Could not generate key. Install cryptography: pip install cryptography"
    fi
    
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo "   Get your key from: https://aistudio.google.com/"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Ready to deploy with Docker:"
echo "   docker compose up --build"
echo ""
echo "🔧 Or run locally:"
echo "   Backend:  cd backend && pip install -r requirements.txt && uvicorn main:app --reload"
echo "   Frontend: cd frontend && npm install && npm run dev"
