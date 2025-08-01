#!/bin/bash

echo "🚀 Starting SpyroSolutions RAG Web Interface"
echo "==========================================="

# Check if the main API is running
echo "Checking if SpyroSolutions API is running on port 8000..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health -H "X-API-Key: spyro-secret-key-123" | grep -q "200"; then
    echo "✅ SpyroSolutions API is running"
else
    echo "❌ SpyroSolutions API is not running on port 8000"
    echo "Please start it first with:"
    echo "  cd .. && python3 enhanced_spyro_api.py"
    exit 1
fi

# Start backend
echo ""
echo "Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || {
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
}

python main.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 2

# Start frontend
echo ""
echo "Starting frontend..."
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo ""
echo "==========================================="
echo "✅ Web UI starting..."
echo ""
echo "Backend API: http://localhost:8001"
echo "Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "==========================================="

# Start frontend (this will block)
npm start

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT