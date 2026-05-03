#!/bin/bash

echo "╔════════════════════════════════════════════════╗"
echo "║   Razorpay Payment Integration Installer      ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip found"
echo ""

# Install Razorpay
echo "📦 Installing Razorpay..."
pip install razorpay || pip3 install razorpay

if [ $? -eq 0 ]; then
    echo "✅ Razorpay installed successfully"
else
    echo "❌ Failed to install Razorpay"
    exit 1
fi

echo ""

# Install other dependencies
echo "📦 Installing other dependencies..."
pip install python-jose[cryptography] passlib[bcrypt] || pip3 install python-jose[cryptography] passlib[bcrypt]

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║         Installation Complete! ✅              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start the server:"
echo "   python main.py"
echo ""
echo "2. Open browser:"
echo "   http://localhost:8000"
echo ""
echo "3. Test payment with test card:"
echo "   Card: 4111 1111 1111 1111"
echo "   CVV: 123"
echo "   Expiry: 12/25"
echo ""
echo "📖 Documentation:"
echo "   - Quick Guide: PAYMENT_SETUP_QUICK_GUIDE.md"
echo "   - Full Guide: RAZORPAY_INTEGRATION_GUIDE.md"
echo "   - Summary: RAZORPAY_COMPLETE_SUMMARY.md"
echo ""
echo "✨ Happy Testing!"
