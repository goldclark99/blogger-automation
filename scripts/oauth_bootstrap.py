from __future__ import annotations

import argparse
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/blogger"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Blogger OAuth refresh token for one Google account")
    parser.add_argument("client_secret", type=Path)
    parser.add_argument("--label", required=True, help="Account label, for example english or thai")
    args = parser.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(str(args.client_secret), SCOPES)
    credentials = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    print(
        json.dumps(
            {
                "label": args.label,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "refresh_token": credentials.refresh_token,
                "scope": SCOPES,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

