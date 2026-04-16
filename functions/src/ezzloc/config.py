import os
import dotenv

# Load environment variables
dotenv.load_dotenv(override=True)

# Ezzloc API Configuration
USERNAME = os.getenv("EZZLOC_USERNAME") or "placeholder"
PASSWORD = os.getenv("EZZLOC_PASSWORD")
BASE_URL = os.getenv("EZZLOC_BASE_URL", "https://www.ezzloc.net/prod-api")
LOGIN_URL = os.getenv("EZZLOC_LOGIN_URL", "https://www.ezzloc.net/prod-api/login")
LANGUANGE = os.getenv("EZZLOC_LANGUANGE", "en")
LANGUAGE_TYPE_VALUE = os.getenv("EZZLOC_LANGUAGE_TYPE_VALUE", "en")

# Device API Configuration (skeleton)
PAGESIZE_DEVICES = int(os.getenv("EZZLOC_PAGESIZE_DEVICES", "100"))
ACCOUNT_ID = os.getenv("EZZLOC_ACCOUNT_ID", "placeholder")
NEED_COUNT = os.getenv("EZZLOC_NEED_COUNT", "true")
STATUS = os.getenv("EZZLOC_STATUS", "-1")

# Output Configuration
PREFIX = os.getenv("EZZLOC_PREFIX", "ezzloc_devices")
