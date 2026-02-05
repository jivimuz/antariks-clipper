#!/bin/bash
# Check if required ports are available

echo "Checking port availability..."
echo ""

check_port() {
    PORT=$1
    NAME=$2
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "❌ Port $PORT ($NAME) is already in use"
        echo "   Process: $(lsof -Pi :$PORT -sTCP:LISTEN -t | xargs ps -p | tail -1)"
        echo "   To free this port: kill $(lsof -Pi :$PORT -sTCP:LISTEN -t)"
        return 1
    else
        echo "✅ Port $PORT ($NAME) is available"
        return 0
    fi
}

ALL_FREE=true

# Check backend port
if ! check_port 8000 "Backend API"; then
    ALL_FREE=false
fi

# Check frontend port
if ! check_port 3000 "Frontend/Next.js"; then
    ALL_FREE=false
fi

echo ""

if [ "$ALL_FREE" = true ]; then
    echo "✅ All required ports are available!"
    echo "You can now run: cd frontend && npm run electron-dev"
    exit 0
else
    echo "⚠️  Some ports are in use. Please free them before starting."
    exit 1
fi
