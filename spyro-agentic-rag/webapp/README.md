# SpyroSolutions Agentic RAG Web Application

A React-based web interface for interacting with the SpyroSolutions Agentic RAG system.

## Features

- 🤖 Chat interface for natural language queries
- 🔍 Automatic tool detection and visualization
- ⚡ Real-time response streaming
- 📊 Execution metadata display
- 🎨 Modern, responsive UI

## Prerequisites

- Node.js 16+ and npm
- SpyroSolutions Agentic RAG API running on http://localhost:8000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Update the `.env` file with your API key if needed.

## Running the Application

### Development Mode

```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000).

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Configuration

### Environment Variables

- `REACT_APP_API_URL`: The URL of the SpyroSolutions API (default: http://localhost:8000)
- `REACT_APP_API_KEY`: API key for authentication

## Usage

1. Ensure the SpyroSolutions Agentic RAG API is running
2. Start the web application
3. Use the chat interface to ask questions about:
   - SpyroSolutions products (SpyroCloud, SpyroAI, SpyroSecure)
   - Customer information and subscriptions
   - Financial metrics and ARR
   - Teams and projects
   - Business risks and objectives

### Example Queries

- "What features does SpyroCloud include?"
- "Which customers have subscriptions over $5M?"
- "Tell me about SpyroAI capabilities"
- "What are the top risks for our objectives?"
- "Show me all teams and their projects"

## Architecture

The web app communicates with the FastAPI backend through:
- `POST /query` - Submit queries and receive AI-generated responses
- `GET /health` - Check API availability
- Authentication via X-API-Key header

## Development

### Project Structure

```
webapp/
├── public/         # Static assets
├── src/
│   ├── App.tsx    # Main application component
│   ├── App.css    # Application styles
│   └── index.tsx  # Entry point
├── package.json   # Dependencies and scripts
└── tsconfig.json  # TypeScript configuration
```

### Key Components

- **App.tsx**: Main chat interface with message history and tool visualization
- **Message Interface**: Displays user queries and AI responses with metadata
- **Tool Detection**: Automatically detects which RAG tools were used based on response content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Part of the SpyroSolutions Agentic RAG system.