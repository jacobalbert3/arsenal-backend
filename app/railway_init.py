from app.init_db import initialize_db
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["ENV"] = "production"
initialize_db()
