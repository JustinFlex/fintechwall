"""WebSocket endpoints for real-time market data streaming."""

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.data_manager import get_data_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.data_manager = get_data_manager()
        self.broadcast_task = None

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

        # Send initial data
        try:
            initial_data = await self.data_manager.get_market_snapshot()
            await websocket.send_json({
                "type": "snapshot",
                "data": initial_data
            })
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")

        # Start broadcasting if this is the first connection
        if len(self.active_connections) == 1:
            await self.start_broadcasting()

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

        # Stop broadcasting if no connections remain
        if len(self.active_connections) == 0:
            await self.stop_broadcasting()

    async def send_to_all(self, message: dict) -> None:
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.discard(connection)

    async def start_broadcasting(self) -> None:
        """Start periodic data broadcasting."""
        if self.broadcast_task is not None:
            return

        logger.info("Starting WebSocket data broadcasting")

        async def broadcast_loop():
            while self.active_connections:
                try:
                    # Fetch latest market data
                    market_data = await self.data_manager.get_market_snapshot()

                    # Send to all connected clients
                    await self.send_to_all({
                        "type": "update",
                        "data": market_data
                    })

                    # Wait before next broadcast
                    await asyncio.sleep(15)  # 15 seconds interval

                except Exception as e:
                    logger.error(f"Error in broadcast loop: {e}")
                    await asyncio.sleep(5)  # Shorter wait on error

            logger.info("Broadcast loop ended - no active connections")

        self.broadcast_task = asyncio.create_task(broadcast_loop())

    async def stop_broadcasting(self) -> None:
        """Stop periodic data broadcasting."""
        if self.broadcast_task:
            self.broadcast_task.cancel()
            self.broadcast_task = None
            logger.info("WebSocket data broadcasting stopped")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time market data streaming."""
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and handle client messages
            try:
                # Wait for client messages (ping/pong, etc.)
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle client messages
                try:
                    data = json.loads(message)
                    await handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, data: dict) -> None:
    """Handle messages from WebSocket clients."""
    message_type = data.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_json({"type": "pong"})

    elif message_type == "subscribe":
        # Handle subscription requests
        subscription = data.get("subscription", "all")
        logger.info(f"Client subscribed to: {subscription}")

        # Send specific data based on subscription
        if subscription == "a-shares":
            indices_data = await manager.data_manager.get_a_share_indices()
            await websocket.send_json({
                "type": "a-shares-data",
                "data": indices_data
            })

    elif message_type == "request_snapshot":
        # Send fresh snapshot on request
        try:
            snapshot = await manager.data_manager.get_market_snapshot()
            await websocket.send_json({
                "type": "snapshot",
                "data": snapshot
            })
        except Exception as e:
            logger.error(f"Error sending snapshot: {e}")
            await websocket.send_json({
                "type": "error",
                "message": "Failed to fetch snapshot"
            })

    else:
        logger.warning(f"Unknown message type: {message_type}")


# Additional endpoint for connection status
@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return {
        "active_connections": len(manager.active_connections),
        "broadcasting": manager.broadcast_task is not None and not manager.broadcast_task.done()
    }