from app.init_db import initialize_db
from dotenv import load_dotenv
import os

# WHEN USE? Run after changing schema or want to reset the db.
# run MANUALLY: python -m app.railway_init 

load_dotenv()
#sets environment to production
os.environ["ENV"] = "production"
#starts db 
initialize_db()