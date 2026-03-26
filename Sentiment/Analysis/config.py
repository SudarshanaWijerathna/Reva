import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Retrieve environment variables

NEWS_API = os.getenv("NEWS_API")
DB_LINK = os.getenv("DB_LINK")
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").strip().lower() == "true"


# Validate required environment variables
if ENABLE_SCHEDULER:
    if not NEWS_API:
        raise ValueError("NEWS_API is not set in the environment variables.")
    if not DB_LINK:
        raise ValueError("DB_LINK is not set in the environment variables.")
