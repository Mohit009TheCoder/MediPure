#!/bin/bash

# Medipure Startup Script

echo "🏥 Starting Medipure Healthcare System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the server
echo ""
echo "🚀 Starting server on http://localhost:8000"
echo ""
echo "✅ Server is running!"
echo "   - Homepage: http://localhost:8000"
echo "   - Login: http://localhost:8000/login"
echo "   - Admin: admin@medipure.com / admin123"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

python3 main.py
