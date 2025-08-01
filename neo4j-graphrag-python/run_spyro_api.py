#!/usr/bin/env python3
"""
Run SpyroSolutions Semantic Model API
"""

import uvicorn
from spyro_semantic_model_implementation import app

if __name__ == "__main__":
    print("Starting SpyroSolutions Semantic Model API...")
    print("API will be available at: http://localhost:8000")
    print("Documentation at: http://localhost:8000/docs")
    print("-" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)