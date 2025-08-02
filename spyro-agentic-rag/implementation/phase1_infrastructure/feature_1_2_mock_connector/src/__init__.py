"""Mock Data Connector for testing the ingestion pipeline"""

from .mock_connector import MockConnector
from .data_generator import DataGenerator

__all__ = ["MockConnector", "DataGenerator"]