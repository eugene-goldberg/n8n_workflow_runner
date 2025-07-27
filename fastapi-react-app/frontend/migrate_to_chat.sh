#!/bin/bash

echo "Migrating frontend to include AI Chat..."

# Backup current App.tsx
if [ -f "src/App.tsx" ]; then
    cp src/App.tsx src/App_backup.tsx
    echo "✓ Backed up current App.tsx to App_backup.tsx"
fi

# Create components directory if it doesn't exist
mkdir -p src/components
mkdir -p src/hooks

# Copy new version
cp src/App_with_chat.tsx src/App.tsx
echo "✓ Updated App.tsx with Chat integration"

# Update environment files
if [ ! -f ".env.local" ]; then
    echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
    echo "REACT_APP_WS_URL=ws://localhost:8000/ws" >> .env.local
    echo "✓ Created .env.local with WebSocket configuration"
fi

# Update production environment
echo "REACT_APP_API_URL=http://srv928466.hstgr.cloud:8080" > .env.production
echo "REACT_APP_WS_URL=ws://srv928466.hstgr.cloud:8080/ws" >> .env.production
echo "✓ Updated .env.production with WebSocket URL"

echo ""
echo "Migration complete! New features added:"
echo "- AI Chat component with WebSocket support"
echo "- Real-time messaging interface"
echo "- Connection status indicator"
echo "- Message history with different types"
echo ""
echo "To install dependencies and run:"
echo "  npm install"
echo "  npm start"