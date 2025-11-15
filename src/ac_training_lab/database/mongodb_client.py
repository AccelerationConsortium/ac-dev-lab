"""
MongoDB client and connection management for AC Training Lab

This module provides MongoDB connection utilities and basic database operations
for storing Bayesian Optimization experiment data.
"""

import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for AC Training Lab experiments"""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "ac_training_lab",
        host: str = "localhost",
        port: int = 27017,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize MongoDB client
        
        Args:
            connection_string: Full MongoDB connection string (overrides other params)
            database_name: Name of the database to use
            host: MongoDB host (default: localhost)
            port: MongoDB port (default: 27017)
            username: Optional username for authentication
            password: Optional password for authentication
            **kwargs: Additional pymongo.MongoClient parameters
        """
        self.database_name = database_name
        self._client = None
        self._database = None
        
        # Build connection string if not provided
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = self._build_connection_string(
                host, port, username, password
            )
        
        # Store additional client parameters
        self.client_kwargs = kwargs
        
    def _build_connection_string(
        self, 
        host: str, 
        port: int, 
        username: Optional[str], 
        password: Optional[str]
    ) -> str:
        """Build MongoDB connection string from components"""
        if username and password:
            # URL encode username and password to handle special characters
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            return f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}"
        else:
            return f"mongodb://{host}:{port}"
    
    @classmethod
    def from_env(cls, database_name: str = "ac_training_lab") -> 'MongoDBClient':
        """
        Create MongoDB client from environment variables
        
        Expected environment variables:
        - MONGODB_URI: Full connection string (optional)
        - MONGODB_HOST: Host (default: localhost)
        - MONGODB_PORT: Port (default: 27017)
        - MONGODB_USERNAME: Username (optional)
        - MONGODB_PASSWORD: Password (optional)
        - MONGODB_DATABASE: Database name (optional)
        """
        connection_string = os.getenv("MONGODB_URI")
        host = os.getenv("MONGODB_HOST", "localhost")
        port = int(os.getenv("MONGODB_PORT", "27017"))
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")
        db_name = os.getenv("MONGODB_DATABASE", database_name)
        
        return cls(
            connection_string=connection_string,
            database_name=db_name,
            host=host,
            port=port,
            username=username,
            password=password
        )
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MongoDB at {self.connection_string}")
            self._client = MongoClient(self.connection_string, **self.client_kwargs)
            
            # Test the connection
            self._client.admin.command('ping')
            
            # Get database reference
            self._database = self._client[self.database_name]
            
            logger.info(f"Successfully connected to MongoDB database '{self.database_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._database = None
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Disconnected from MongoDB")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MongoDB"""
        return self._client is not None and self._database is not None
    
    @property
    def database(self) -> Database:
        """Get database instance"""
        if not self.is_connected:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        return self._database
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get collection instance"""
        return self.database[collection_name]
    
    def create_indexes(self):
        """Create recommended indexes for BO experiment collections"""
        if not self.is_connected:
            logger.warning("Not connected to MongoDB. Skipping index creation.")
            return
            
        try:
            # Experiments collection indexes
            experiments_collection = self.get_collection("experiments")
            experiments_collection.create_index("experiment_id", unique=True)
            experiments_collection.create_index("status")
            experiments_collection.create_index("created_at")
            experiments_collection.create_index("flow_run_id")
            
            # Trials collection indexes
            trials_collection = self.get_collection("trials")
            trials_collection.create_index("trial_id", unique=True)
            trials_collection.create_index("experiment_id")
            trials_collection.create_index([("experiment_id", 1), ("trial_index", 1)], unique=True)
            trials_collection.create_index("status")
            trials_collection.create_index("suggested_at")
            
            # Results collection indexes
            results_collection = self.get_collection("results")
            results_collection.create_index("experiment_id", unique=True)
            results_collection.create_index("created_at")
            
            logger.info("Successfully created MongoDB indexes")
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test MongoDB connection and return status information
        
        Returns:
            Dictionary with connection status and server info
        """
        try:
            if not self.is_connected:
                self.connect()
            
            if not self.is_connected:
                return {"connected": False, "error": "Failed to connect"}
            
            # Get server information
            server_info = self._client.server_info()
            db_stats = self.database.command("dbstats")
            
            return {
                "connected": True,
                "database_name": self.database_name,
                "server_version": server_info.get("version"),
                "collections": self.database.list_collection_names(),
                "database_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Global client instance for easy access
_global_client: Optional[MongoDBClient] = None


def get_mongodb_client() -> MongoDBClient:
    """Get or create global MongoDB client instance"""
    global _global_client
    
    if _global_client is None:
        _global_client = MongoDBClient.from_env()
    
    return _global_client


def set_mongodb_client(client: MongoDBClient):
    """Set global MongoDB client instance"""
    global _global_client
    _global_client = client