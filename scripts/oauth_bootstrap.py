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
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Print the authorization URL instead of opening the default browser",
    )
    parser.add_argument(
        "--url-output",
        type=Path,
        help="Private file that temporarily receives the authorization URL",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Private output JSON path; defaults to oauth-output-<label>.json",
    )
    args = parser.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(str(args.client_secret), SCOPES)
    if args.url_output:
        original_authorization_url = flow.authorization_url

        def authorization_url(*url_args, **url_kwargs):
            url, state = original_authorization_url(*url_args, **url_kwargs)
            args.url_output.write_text(url, encoding="utf-8")
            return url, state

        flow.authorization_url = authorization_url
    credentials = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        open_browser=not args.no_browser,
    )
    output = args.output or Path(f"oauth-output-{args.label}.json")
    output.write_text(
        json.dumps(
            {
                "label": args.label,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "refresh_token": credentials.refresh_token,
                "scope": SCOPES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"OAuth credentials saved locally: {output.resolve()}")
    print("Keep this file private. Do not commit or share its contents.")


if __name__ == "__main__":
    main()
