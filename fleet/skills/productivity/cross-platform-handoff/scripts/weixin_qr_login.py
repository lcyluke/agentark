#!/usr/bin/env python3
"""WeChat iLink QR login: fetch QR from iLink API, print ASCII + save PNG, poll for confirmation.

Usage:
    /Users/Mac/.hermes/hermes-agent/venv/bin/python3 weixin_qr_login.py

Requires: aiohttp, cryptography, qrcode, Pillow (in Hermes venv)
"""

import asyncio, sys, os, time

sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))

from gateway.platforms.weixin import (
    ILINK_BASE_URL, _make_ssl_connector, _api_get,
    save_weixin_account,
)
from hermes_constants import get_hermes_home
from qrcode import QRCode
from qrcode.constants import ERROR_CORRECT_M


def print_ascii_qr(data: str):
    qr = QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=1, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


async def main():
    import aiohttp
    hermes_home = get_hermes_home()

    print("=" * 60)
    print("  Hermes x WeChat QR Login")
    print("=" * 60)

    async with aiohttp.ClientSession(trust_env=True, connector=_make_ssl_connector()) as session:
        deadline = time.monotonic() + 300

        while time.monotonic() < deadline:
            # Fetch QR
            try:
                qr_resp = await _api_get(session, base_url=ILINK_BASE_URL,
                                          endpoint="ilink/bot/get_bot_qrcode?bot_type=3",
                                          timeout_ms=35000)
            except Exception as exc:
                print(f"\nFailed to fetch QR: {exc}")
                return 1

            qrcode_value = str(qr_resp.get("qrcode") or "")
            liteapp_url = str(qr_resp.get("qrcode_img_content") or "")
            scan_data = liteapp_url if liteapp_url else qrcode_value

            if not qrcode_value:
                print("No QR data received")
                return 1

            print()
            print_ascii_qr(scan_data)
            print("-" * 60)
            print(f"  Scan with WeChat, or open: {scan_data}")
            print("-" * 60)
            print()
            print("  Waiting", end="", flush=True)

            current_base = ILINK_BASE_URL
            qr_deadline = min(time.monotonic() + 120, deadline)

            while time.monotonic() < qr_deadline:
                try:
                    resp = await _api_get(session, base_url=current_base,
                                           endpoint=f"ilink/bot/get_qrcode_status?qrcode={qrcode_value}",
                                           timeout_ms=35000)
                except asyncio.TimeoutError:
                    await asyncio.sleep(1); continue
                except Exception:
                    await asyncio.sleep(1); continue

                status = str(resp.get("status") or "wait")

                if status == "wait":
                    print(".", end="", flush=True)
                elif status == "scaned":
                    print("\n  Scanned - confirm in WeChat...")
                elif status == "scaned_but_redirect":
                    rh = str(resp.get("redirect_host") or "")
                    if rh: current_base = f"https://{rh}"
                elif status == "expired":
                    print("\n  QR expired, refreshing...")
                    break
                elif status == "confirmed":
                    account_id = str(resp.get("ilink_bot_id") or "")
                    token = str(resp.get("bot_token") or "")
                    base_url = str(resp.get("baseurl") or ILINK_BASE_URL)
                    user_id = str(resp.get("ilink_user_id") or "")

                    if not account_id or not token:
                        print("\n  Incomplete credentials")
                        return 1

                    save_weixin_account(hermes_home, account_id=account_id, token=token,
                                        base_url=base_url, user_id=user_id)

                    # Write .env
                    env_path = os.path.join(hermes_home, ".env")
                    lines = []
                    if os.path.exists(env_path):
                        with open(env_path) as f:
                            lines = [l for l in f.read().splitlines() if not l.startswith("WEIXIN_")]
                    lines.append(f"WEIXIN_ACCOUNT_ID={account_id}")
                    lines.append(f"WEIXIN_TOKEN={token}")
                    if base_url != ILINK_BASE_URL:
                        lines.append(f"WEIXIN_BASE_URL={base_url}")
                    lines.append("WEIXIN_DM_POLICY=open")
                    lines.append(f"WEIXIN_ALLOWED_USERS={user_id}")
                    lines.append("")
                    with open(env_path, "w") as f:
                        f.write("\n".join(lines))

                    print(f"\n\n  OK! Bot ID: {account_id}")
                    print(f"  Env written: {env_path}")
                    print(f"  Next: hermes gateway restart")
                    return 0

                await asyncio.sleep(1)
            else:
                print("\n  Polling timed out")
                return 1

        print("\n  Overall timeout")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
