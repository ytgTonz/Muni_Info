from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from src.config import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,
                retryWrites=True
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[Config.MONGODB_DB_NAME]
            logger.info(f"Successfully connected to MongoDB database: {Config.MONGODB_DB_NAME}")
            
            # Create indexes for better performance
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Create indexes for complaints collection
            complaints_collection = self.db.complaints
            
            # Create compound index for reference_id (unique)
            complaints_collection.create_index("reference_id", unique=True)
            
            # Create index for phone number lookups
            complaints_collection.create_index("sender")
            
            # Create index for status filtering
            complaints_collection.create_index("status")
            
            # Create index for timestamp sorting
            complaints_collection.create_index("timestamp")
            
            # Create index for complaint type filtering
            complaints_collection.create_index("complaint_type")
            
            # Create indexes for other collections
            self.db.announcements.create_index("municipality")
            self.db.announcements.create_index("created_at")
            self.db.announcements.create_index("priority")
            
            self.db.service_ratings.create_index("service_type")
            self.db.service_ratings.create_index("municipality")
            self.db.service_ratings.create_index("created_at")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        if self.db is None:
            self._connect()
        return self.db[collection_name]
    
    def close_connection(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database service instance
db_service = DatabaseService()