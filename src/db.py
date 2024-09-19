from flask_pymongo import MongoClient
from dotenv import load_dotenv
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

client = MongoClient(
    os.getenv('MONGO_URI') + "?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
)
db = client[os.getenv('DB_NAME')]                  
