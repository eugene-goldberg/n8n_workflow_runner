# FastAPI + React Todo App

A simple todo application built with FastAPI backend and React TypeScript frontend.

## Setup

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd fastapi-react-app/backend
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI server:
   ```bash
   python3 main.py
   ```

The API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

### Frontend (React)

1. In a new terminal, navigate to the frontend directory:
   ```bash
   cd fastapi-react-app/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```

The app will open at http://localhost:3000

## Features

- Create, read, update, and delete todo items
- Mark items as completed
- Real-time updates between frontend and backend
- Clean, responsive UI

## API Endpoints

- `GET /` - Welcome message
- `GET /api/items` - Get all items
- `GET /api/items/{id}` - Get specific item
- `POST /api/items` - Create new item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item