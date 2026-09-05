"""
Automated Sync Bridge for Leghe Fantacalcio API.
Connects to apileague.fantacalcio.it to fetch rosters, calendars, opponent lineups, and live scores.
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
CONFIG_FILE = WORKSPACE_ROOT / "config_lega.json"

DEFAULT_APP_KEY = "ICiELOObd5DF5uJEATi77CRvHiiRuMU0"
DEFAULT_COMPETITION_ID = 539125
DEFAULT_LEAGUE_ALIAS = "fanta-bro-cx"


class LegheSyncClient:
    def __init__(
        self,
        app_key: str = DEFAULT_APP_KEY,
        token: Optional[str] = None,
        competition_id: int = DEFAULT_COMPETITION_ID,
        alias_lega: str = DEFAULT_LEAGUE_ALIAS
    ):
        self.app_key = app_key
        self.competition_id = competition_id
        self.alias_lega = alias_lega
        self.token = token or self._load_saved_token()
        self.base_url = "https://apileague.fantacalcio.it"

    def _load_saved_token(self) -> Optional[str]:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("bearer_token")
            except Exception:
                pass
        return os.environ.get("FANTA_BEARER_TOKEN")

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        headers = {
            "accept": "application/json, text/plain, */*",
            "app_key": self.app_key,
            "origin": "https://leghe.fantacalcio.it",
            "referer": "https://leghe.fantacalcio.it/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        }
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"HTTP error {e.code} for {url}: {err_body}")
            raise RuntimeError(f"Leghe API error {e.code}: {err_body}")
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        return self._make_request("/onboarding/v1/league/status")

    def get_rosters(self) -> Dict[str, Any]:
        return self._make_request("/onboarding/v1/league/teams", {"page": 1, "division": "A"})

    def get_calendar(self) -> Dict[str, Any]:
        return self._make_request(f"/onboarding/v1/league/competition/calendar/{self.competition_id}")


def main():
    parser = argparse.ArgumentParser(description="Leghe Fantacalcio API Sync CLI")
    parser.add_argument("--status", action="store_true", help="Check league status")
    parser.add_argument("--token", type=str, help="Save Bearer token for automated sync")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if args.token:
        cfg = {"bearer_token": args.token, "app_key": DEFAULT_APP_KEY, "competition_id": DEFAULT_COMPETITION_ID}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print(f"✅ Bearer token saved to {CONFIG_FILE}")
        return

    client = LegheSyncClient()
    try:
        status = client.get_status()
        print("✅ Connection to Leghe Fantacalcio API SUCCESS!")
        print(json.dumps(status, indent=2))
    except Exception as e:
        print(f"⚠️ Connection status: {e}")

if __name__ == "__main__":
    main()
