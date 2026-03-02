"""
WebSocket Connection Management
Real-time workflow monitoring and status updates
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Set, List, Any, Optional
from datetime import datetime

# Try to import FastAPI components, but handle gracefully for core functionality tests
try:
    from fastapi import WebSocket, WebSocketDisconnect
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Define dummy classes for core functionality
    class WebSocket:
        pass
    class WebSocketDisconnect(Exception):
        pass

import yaml

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager for real-time monitoring"""

    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}

        # Workflow to connection mapping (one workflow can have multiple viewers)
        self.workflow_subscribers: Dict[str, Set[str]] = {}

        # Execution to connection mapping (for execution-specific monitoring)
        self.execution_connections: Dict[str, Set[str]] = {}

        # Background monitoring tasks
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str) -> str:
        """
        Establish WebSocket connection and subscribe to workflow

        Args:
            websocket: WebSocket connection
            workflow_id: Workflow identifier to monitor

        Returns:
            Connection identifier
        """
        try:
            await websocket.accept()

            connection_id = f"{workflow_id}_{id(websocket)}"
            self.active_connections[connection_id] = websocket

            # Subscribe to workflow
            if workflow_id not in self.workflow_subscribers:
                self.workflow_subscribers[workflow_id] = set()
            self.workflow_subscribers[workflow_id].add(connection_id)

            logger.info(f"WebSocket connected: {connection_id} for workflow: {workflow_id}")

            # Send connection confirmation
            await websocket.send_text(json.dumps({
                "type": "connected",
                "connection_id": connection_id,
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat()
            }))

            # Start monitoring task for this workflow
            await self._start_workflow_monitoring(workflow_id)

            return connection_id

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def connect_to_execution(self, websocket: WebSocket, execution_id: str) -> str:
        """
        Establish WebSocket connection for execution-specific monitoring

        Args:
            websocket: WebSocket connection
            execution_id: Execution identifier to monitor

        Returns:
            Connection identifier
        """
        try:
            await websocket.accept()

            connection_id = f"exec_{execution_id}_{id(websocket)}"
            self.active_connections[connection_id] = websocket

            # Subscribe to execution
            if execution_id not in self.execution_connections:
                self.execution_connections[execution_id] = set()
            self.execution_connections[execution_id].add(connection_id)

            logger.info(f"WebSocket connected: {connection_id} for execution: {execution_id}")

            # Send connection confirmation
            await websocket.send_text(json.dumps({
                "type": "connected",
                "connection_id": connection_id,
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat()
            }))

            return connection_id

        except Exception as e:
            logger.error(f"WebSocket execution connection failed: {e}")
            raise

    def disconnect(self, workflow_id: str, connection_id: str):
        """
        Handle WebSocket disconnection
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if workflow_id in self.workflow_subscribers:
            if connection_id in self.workflow_subscribers[workflow_id]:
                self.workflow_subscribers[workflow_id].remove(connection_id)

            # If no more subscribers, stop monitoring
            if not self.workflow_subscribers[workflow_id]:
                asyncio.create_task(self._stop_workflow_monitoring(workflow_id))
                del self.workflow_subscribers[workflow_id]

        logger.info(f"WebSocket disconnected: {connection_id} for workflow: {workflow_id}")

    def disconnect_from_execution(self, execution_id: str, connection_id: str):
        """
        Handle execution WebSocket disconnection
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if execution_id in self.execution_connections:
            if connection_id in self.execution_connections[execution_id]:
                self.execution_connections[execution_id].remove(connection_id)

            # Clean up empty execution connections
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]

        logger.info(f"WebSocket disconnected: {connection_id} for execution: {execution_id}")

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """
        Send message to specific connection
        """
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps({
                    **message,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                # Connection may be dead, clean up
                self._cleanup_dead_connection(connection_id)

    async def broadcast_to_workflow(self, workflow_id: str, message: Dict[str, Any]):
        """
        Broadcast message to all subscribers of a workflow
        """
        if workflow_id not in self.workflow_subscribers:
            logger.warning(f"No subscribers for workflow: {workflow_id}")
            return

        dead_connections = []

        for connection_id in self.workflow_subscribers[workflow_id]:
            if connection_id in self.active_connections:
                try:
                    await self.active_connections[connection_id].send_text(json.dumps({
                        **message,
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    dead_connections.append(connection_id)
            else:
                dead_connections.append(connection_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            self._cleanup_dead_connection(conn_id)

    async def broadcast_to_execution(self, execution_id: str, message: Dict[str, Any]):
        """
        Broadcast message to all connections monitoring an execution
        """
        if execution_id not in self.execution_connections:
            # No connected listeners, silently skip
            return

        dead_connections = []

        for connection_id in self.execution_connections[execution_id]:
            if connection_id in self.active_connections:
                try:
                    await self.active_connections[connection_id].send_text(json.dumps({
                        **message,
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Failed to broadcast to execution {connection_id}: {e}")
                    dead_connections.append(connection_id)
            else:
                dead_connections.append(connection_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            self._cleanup_dead_connection(conn_id)

    async def _start_workflow_monitoring(self, workflow_id: str):
        """
        Start background task to monitor workflow execution
        """
        if workflow_id in self.monitoring_tasks:
            # Already monitoring
            return

        task = asyncio.create_task(self._monitor_workflow(workflow_id))
        self.monitoring_tasks[workflow_id] = task
        logger.info(f"Started monitoring workflow: {workflow_id}")

    async def _stop_workflow_monitoring(self, workflow_id: str):
        """
        Stop background monitoring task for workflow
        """
        if workflow_id in self.monitoring_tasks:
            task = self.monitoring_tasks[workflow_id]
            task.cancel()
            del self.monitoring_tasks[workflow_id]
            logger.info(f"Stopped monitoring workflow: {workflow_id}")

    async def _monitor_workflow(self, workflow_id: str):
        """
        Monitor workflow execution status and file changes
        """
        workflow_dir = Path("data/workflows") / workflow_id

        if not workflow_dir.exists():
            logger.warning(f"Workflow directory not found: {workflow_dir}")
            return

        try:
            status_file = workflow_dir / ".engine" / "status"
            log_file = workflow_dir / "logs" / "engine.log"

            last_status = {}
            last_log_position = 0

            while workflow_id in self.workflow_subscribers:
                try:
                    # Check for status updates
                    if status_file.exists():
                        current_status = await self._read_status_file(status_file)
                        if current_status != last_status:
                            await self.broadcast_to_workflow(workflow_id, {
                                "type": "status_update",
                                "workflow_id": workflow_id,
                                "status": current_status
                            })
                            last_status = current_status

                    # Check for new log entries
                    if log_file.exists():
                        new_logs = await self._read_new_log_lines(
                            log_file, last_log_position
                        )
                        if new_logs:
                            await self.broadcast_to_workflow(workflow_id, {
                                "type": "log_update",
                                "workflow_id": workflow_id,
                                "lines": new_logs
                            })
                            last_log_position += len(new_logs)

                    # Check if workflow is complete
                    if current_status.get("status") in ["completed", "failed"]:
                        await self.broadcast_to_workflow(workflow_id, {
                            "type": "execution_complete",
                            "workflow_id": workflow_id,
                            "status": current_status.get("status"),
                            "message": f"Workflow {current_status.get('status')}"
                        })
                        break

                    await asyncio.sleep(1)  # Check every second

                except asyncio.CancelledError:
                    logger.info(f"Monitoring cancelled for workflow: {workflow_id}")
                    break
                except Exception as e:
                    logger.error(f"Error monitoring workflow {workflow_id}: {e}")
                    await asyncio.sleep(5)  # Wait longer on errors

        except Exception as e:
            logger.error(f"Fatal error monitoring workflow {workflow_id}: {e}")

    async def _read_status_file(self, status_file: Path) -> Dict[str, Any]:
        """
        Read and parse FlowEngine status file
        """
        try:
            with open(status_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.debug(f"Failed to read status file {status_file}: {e}")
            return {}

    async def _read_new_log_lines(self, log_file: Path, start_position: int,
                                  max_lines: int = 100) -> List[str]:
        """
        Read new lines from log file
        """
        try:
            with open(log_file, 'r') as f:
                f.seek(start_position)
                lines = []

                # Read lines efficiently
                for _ in range(max_lines):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.rstrip('\n'))

                return lines
        except Exception as e:
            logger.debug(f"Failed to read log file {log_file}: {e}")
            return []

    def _cleanup_dead_connection(self, connection_id: str):
        """
        Clean up dead connection
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Remove from workflow subscriptions
        for workflow_id, subscribers in self.workflow_subscribers.items():
            if connection_id in subscribers:
                subscribers.remove(connection_id)

                # Schedule monitoring stop if no more subscribers (don't await here)
                if not subscribers:
                    # Use create_task to avoid await in sync method
                    import asyncio
                    if workflow_id in self.monitoring_tasks:
                        task = self.monitoring_tasks[workflow_id]
                        if task and not task.done():
                            task.cancel()
                        if workflow_id in self.monitoring_tasks:
                            del self.monitoring_tasks[workflow_id]

    async def websocket_endpoint(self, websocket: WebSocket, workflow_id: str):
        """
        Main WebSocket endpoint handler
        """
        connection_id = None

        try:
            connection_id = await self.connect(websocket, workflow_id)

            # Handle messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Handle different message types
                    await self._handle_client_message(
                        connection_id, workflow_id, message
                    )

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    break

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for workflow: {workflow_id}")
        except Exception as e:
            logger.error(f"WebSocket endpoint error: {e}")
        finally:
            if connection_id:
                self.disconnect(workflow_id, connection_id)

    async def execution_websocket_endpoint(self, websocket: WebSocket, execution_id: str):
        """
        Execution-specific WebSocket endpoint handler for real-time logs and status
        """
        from app.services.runner import execution_manager

        connection_id = None

        try:
            # Verify execution exists
            execution = execution_manager.get(execution_id)
            if not execution:
                await websocket.close(code=4001, reason=json.dumps({"error": "Execution not found"}))
                logger.warning(f"WebSocket rejected: execution {execution_id} not found")
                return

            connection_id = await self.connect_to_execution(websocket, execution_id)

            # Send initial status
            await websocket.send_text(json.dumps({
                "type": "status",
                "status": execution.status,
                "progress": execution.progress,
                "execution_id": execution_id
            }))

            # Send existing logs if any
            if execution.logs:
                for log in execution.logs:
                    await websocket.send_text(json.dumps({
                        "type": "log",
                        "data": log,
                        "execution_id": execution_id
                    }))

            # Keep connection alive and handle ping/pong
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Handle ping/pong
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "execution_id": execution_id
                        }))

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    break

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for execution: {execution_id}")
        except Exception as e:
            logger.error(f"WebSocket endpoint error for execution {execution_id}: {e}")
            try:
                await websocket.close(code=1011, reason=str(e))
            except:
                pass
        finally:
            if connection_id:
                self.disconnect_from_execution(execution_id, connection_id)

    async def _handle_client_message(self, connection_id: str, workflow_id: str,
                                   message: Dict[str, Any]):
        """
        Handle incoming WebSocket messages
        """
        message_type = message.get("type")

        if message_type == "ping":
            await self.send_personal_message(connection_id, {
                "type": "pong",
                "workflow_id": workflow_id
            })
        elif message_type == "subscribe":
            await self.send_personal_message(connection_id, {
                "type": "subscribed",
                "workflow_id": workflow_id,
                "message": f"Subscribed to workflow monitoring"
            })
        elif message_type == "get_status":
            # Send current status immediately
            workflow_dir = Path("data/workflows") / workflow_id
            if workflow_dir.exists():
                status_file = workflow_dir / ".engine" / "status"
                if status_file.exists():
                    current_status = await self._read_status_file(status_file)
                    await self.send_personal_message(connection_id, {
                        "type": "status_update",
                        "workflow_id": workflow_id,
                        "status": current_status
                    })
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")

    async def cleanup_all_connections(self):
        """
        Clean up all connections and monitoring tasks
        """
        logger.info("Cleaning up all WebSocket connections...")

        # Cancel all monitoring tasks
        for workflow_id in list(self.monitoring_tasks.keys()):
            task = self.monitoring_tasks.get(workflow_id)
            if task and not task.done():
                task.cancel()
            if workflow_id in self.monitoring_tasks:
                del self.monitoring_tasks[workflow_id]

        # Close all connections
        for connection_id in list(self.active_connections.keys()):
            try:
                if self.active_connections[connection_id]:
                    await self.active_connections[connection_id].close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")

        # Clear all data
        self.active_connections.clear()
        self.workflow_subscribers.clear()
        self.execution_connections.clear()
        self.monitoring_tasks.clear()

        logger.info("All WebSocket connections cleaned up")

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection statistics
        """
        return {
            "active_connections": len(self.active_connections),
            "monitored_workflows": len(self.workflow_subscribers),
            "monitoring_tasks": len(self.monitoring_tasks),
            "workflow_subscribers": {
                workflow_id: len(subscribers)
                for workflow_id, subscribers in self.workflow_subscribers.items()
            }
        }