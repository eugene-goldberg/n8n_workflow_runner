"""PostgreSQL checkpointer for LangGraph state persistence."""

import logging
from contextlib import contextmanager
from typing import Optional

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
import psycopg

from config.settings import settings

logger = logging.getLogger(__name__)


@contextmanager
def get_postgres_connection():
    """Get a PostgreSQL connection with proper settings for checkpointer."""
    conn = psycopg.connect(
        settings.postgres.pgvector_connection_string,
        autocommit=True,
        row_factory=psycopg.rows.dict_row
    )
    try:
        yield conn
    finally:
        conn.close()


def get_postgres_checkpointer(setup: bool = False) -> PostgresSaver:
    """Get a PostgreSQL checkpointer for LangGraph state persistence.
    
    Args:
        setup: If True, create the necessary database tables on first run.
        
    Returns:
        PostgresSaver instance configured for the application.
    """
    checkpointer = PostgresSaver.from_conn_string(
        settings.postgres.pgvector_connection_string
    )
    
    if setup:
        # Create necessary tables on first run
        with get_postgres_connection() as conn:
            checkpointer.setup()
            logger.info("PostgreSQL checkpointer tables created successfully")
    
    return checkpointer


class CheckpointerManager:
    """Manager class for checkpointer lifecycle."""
    
    def __init__(self):
        self._checkpointer: Optional[PostgresSaver] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the checkpointer, creating tables if needed."""
        if self._initialized:
            return
            
        try:
            # First attempt - try to use existing tables
            self._checkpointer = get_postgres_checkpointer(setup=False)
            # Test the connection
            with get_postgres_connection() as conn:
                conn.execute("SELECT 1")
            self._initialized = True
            logger.info("Connected to existing checkpointer tables")
        except Exception as e:
            # Tables don't exist, create them
            logger.info(f"Creating checkpointer tables: {e}")
            self._checkpointer = get_postgres_checkpointer(setup=True)
            self._initialized = True
    
    @property
    def checkpointer(self) -> PostgresSaver:
        """Get the checkpointer instance, initializing if needed."""
        if not self._initialized:
            self.initialize()
        return self._checkpointer
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self._checkpointer
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._checkpointer:
            self._checkpointer.__exit__(exc_type, exc_val, exc_tb)


# Global checkpointer manager
checkpointer_manager = CheckpointerManager()