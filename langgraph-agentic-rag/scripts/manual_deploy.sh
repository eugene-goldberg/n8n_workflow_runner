#!/bin/bash

# Manual deployment commands for LangGraph Agentic RAG
# Run these commands manually if the automated script fails

echo "Manual deployment steps for LangGraph Agentic RAG"
echo "================================================"
echo ""
echo "1. Create remote directory:"
echo "   ssh root@154.53.57.127 'mkdir -p /root/langgraph-agentic-rag/{app,scripts,tests}'"
echo ""
echo "2. Create subdirectories:"
echo "   ssh root@154.53.57.127 'mkdir -p /root/langgraph-agentic-rag/app/{agent,tools,schemas,monitoring}'"
echo ""
echo "3. Copy files:"
echo "   scp -r app/* root@154.53.57.127:/root/langgraph-agentic-rag/app/"
echo "   scp requirements.txt root@154.53.57.127:/root/langgraph-agentic-rag/"
echo "   scp README.md root@154.53.57.127:/root/langgraph-agentic-rag/"
echo "   scp .env.example root@154.53.57.127:/root/langgraph-agentic-rag/"
echo ""
echo "4. On the remote server:"
echo "   cd /root/langgraph-agentic-rag"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   cp .env.example .env"
echo "   # Edit .env with actual credentials"
echo ""
echo "5. Test the router:"
echo "   python3 -c 'from app.agent.router import DeterministicRouter; r = DeterministicRouter(); print(r.route(\"How much revenue at risk if Disney churns?\"))'"