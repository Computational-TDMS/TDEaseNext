"""
Log Handler - Capture logs from FlowEngine execution

Captures logs from FlowEngine logger and associates them with executions/nodes.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict


class ExecutionLogHandler(logging.Handler):
    """
    Custom log handler that captures FlowEngine logger output.

    Associates logs with execution_id and optionally node_id.
    """
    
    def __init__(self, execution_id: str):
        """
        Initialize log handler.
        
        Args:
            execution_id: Execution ID to associate logs with
        """
        super().__init__()
        self.execution_id = execution_id
        self.logs: List[Dict[str, Any]] = []
        self.node_logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.max_logs = 10000  # Prevent memory issues
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record.

        Args:
            record: Log record from logger
        """
        if len(self.logs) >= self.max_logs:
            # Remove oldest logs if we exceed limit
            self.logs.pop(0)

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "message": self.format(record),
            "execution_id": self.execution_id,
        }

        # Try to extract node_id from log message/context
        node_id = self._extract_node_id(record)
        if node_id:
            log_entry["node_id"] = node_id
            self.node_logs[node_id].append(log_entry)

        self.logs.append(log_entry)

        # Broadcast to WebSocket asynchronously (fire and forget)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                asyncio.create_task(
                    log_collector.broadcast_log_to_websocket(self.execution_id, log_entry)
                )
        except RuntimeError:
            # No event loop or closed, skip WebSocket broadcast
            pass
    
    def _extract_node_id(self, record: logging.LogRecord) -> Optional[str]:
        """
        Try to extract node_id from log record.
        
        Checks record attributes for node_id or rule_name.
        """
        # Check if node_id is in extra fields
        if hasattr(record, "node_id"):
            return record.node_id
        
        # Check if rule_name is in extra fields and extract node_id
        if hasattr(record, "rule_name"):
            rule_name = record.rule_name
            if rule_name.startswith("node_"):
                return rule_name[5:]  # Remove "node_" prefix
        
        # Try to parse from message
        # This is heuristic - may need refinement
        message = record.getMessage()
        if "node_" in message:
            # Simple extraction - look for "node_xxx" pattern
            import re
            match = re.search(r"node_([a-zA-Z0-9_-]+)", message)
            if match:
                return match.group(1)
        
        return None
    
    def get_logs(
        self,
        node_id: Optional[str] = None,
        level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get logs, optionally filtered.
        
        Args:
            node_id: Filter by node ID
            level: Filter by log level
            limit: Limit number of logs returned
            
        Returns:
            List of log entries
        """
        logs = self.logs
        
        if node_id:
            logs = self.node_logs.get(node_id, [])
        
        if level:
            logs = [log for log in logs if log["level"] == level.lower()]
        
        if limit:
            logs = logs[-limit:]  # Return most recent N logs
        
        return logs
    
    def clear(self):
        """Clear all logs."""
        self.logs.clear()
        self.node_logs.clear()


class LogCollector:
    """
    Manages log handlers for multiple executions.
    """

    def __init__(self):
        """Initialize log collector."""
        self.handlers: Dict[str, ExecutionLogHandler] = {}
        self.root_logger = logging.getLogger("tdease.engine")

    async def broadcast_log_to_websocket(self, execution_id: str, log_entry: Dict[str, Any]):
        """
        Broadcast a log entry to WebSocket connections monitoring this execution.

        Args:
            execution_id: Execution ID
            log_entry: Log entry to broadcast
        """
        try:
            from app.core.websocket import manager
            await manager.broadcast_to_execution(execution_id, {
                "type": "log",
                "data": log_entry,
                "execution_id": execution_id
            })
        except Exception as e:
            # WebSocket broadcast failure should not break log collection
            pass  # Silently fail - WebSocket may not be available
    
    def create_handler(self, execution_id: str) -> ExecutionLogHandler:
        """
        Create and register log handler for execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Log handler
        """
        handler = ExecutionLogHandler(execution_id)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.handlers[execution_id] = handler
        self.root_logger.addHandler(handler)
        
        return handler
    
    def get_handler(self, execution_id: str) -> Optional[ExecutionLogHandler]:
        """Get handler for execution ID."""
        return self.handlers.get(execution_id)
    
    def remove_handler(self, execution_id: str):
        """
        Remove and cleanup handler.
        
        Args:
            execution_id: Execution ID
        """
        handler = self.handlers.pop(execution_id, None)
        if handler:
            self.root_logger.removeHandler(handler)
            handler.clear()


# Global log collector instance
log_collector = LogCollector()

