import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.routes import router as api_router
from backend.api.websockets import manager
import asyncio
from backend.simulator import simulation_loop

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME, 
    description="Dynamic Context-Aware Train ETA Predictor Backend using XGBoost Cascade Physics",
    version="0.1.0"
)

# Crucial for Frontend communication bridging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

@app.websocket("/ws/live")
async def websocket_live_updates(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"WS Engine Received Pulse: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WS Engine Disconnected.")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
