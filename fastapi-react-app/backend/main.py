from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import httpx

app = FastAPI(title="Sample FastAPI App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://srv928466.hstgr.cloud", "http://srv928466.hstgr.cloud:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    completed: bool = False
    created_at: Optional[datetime] = None

items_db = []
item_counter = 1

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}

@app.get("/api/items", response_model=List[Item])
def get_items():
    return items_db

@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = next((item for item in items_db if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/api/items", response_model=Item)
def create_item(item: Item):
    global item_counter
    item.id = item_counter
    item.created_at = datetime.now()
    item_counter += 1
    items_db.append(item)
    return item

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item):
    for index, item in enumerate(items_db):
        if item.id == item_id:
            updated_item.id = item_id
            updated_item.created_at = item.created_at
            items_db[index] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": "Item deleted successfully"}

@app.post("/api/workflow/execute")
async def execute_workflow():
    try:
        # Replace with your actual n8n PRODUCTION webhook URL (not test URL)
        # Example: "https://your-n8n-instance.com/webhook/abc123/workflow1"
        # Make sure to use /webhook/ not /webhook-test/
        N8N_WEBHOOK_URL = "https://myhost.com/workflows/workflow1/"
        
        # You can send data to the workflow
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "source": "FastAPI Todo App",
            "action": "manual_trigger"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=workflow_data,
                timeout=30.0
            )
            return {
                "status": "success",
                "workflow_response": {
                    "status_code": response.status_code,
                    "body": response.text
                }
            }
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Workflow execution timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to execute workflow: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)