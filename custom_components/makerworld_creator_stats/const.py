"""Constants for the standalone MakerWorld integration."""

from pathlib import Path
import json

DOMAIN = "makerworld_creator_stats"

# Identify this project unambiguously in all API requests.
CLIENT_NAME = "ha-makerworld-creator-stats"
CLIENT_VERSION = json.loads(
    Path(__file__).with_name("manifest.json").read_text(encoding="utf-8")
)["version"]
USER_AGENT = f"{CLIENT_NAME}/v{CLIENT_VERSION}"

# Beta 2: statistics poll carefully with independent refresh windows.
# The paginated transaction-history import remains disabled.
BASE_URL = "https://api.bambulab.com"
EMAIL_CODE = "/v1/user-service/user/sendemail/code"
LOGIN = "/v1/user-service/user/login"
PROFILE = "/v1/design-user-service/my/profile"
POINTS = "/v1/point-service/point-bill/my?offset=0&limit=1&filter=all"
BOOSTS = "/v1/point-service/boost/boostingright"
