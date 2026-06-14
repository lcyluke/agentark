#!/usr/bin/env python3
"""
Hermes × WeChat QR Login Script

Fetches a QR code from Tencent iLink Bot API, generates a PNG image,
opens it on macOS, and polls for scan confirmation.

Output:
  On success: saves credentials to ~/.hermes/weixin/accounts/ + ~/.hermes/.env
  On failure: non-zero exit

Dependencies installed into Hermes venv:
  aiohttp, cryptography, qrcode, Pillow

See: wechat-integration skill SKILL.md for full setup.
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))

from gateway.platforms.weixin import (
    ILINK_BASE_URL, EP_GET_BOT_QR, EP_GET_QR_STATUS,
    _make_ssl_connector, _api_get,
    save_weixin_account,
)
from hermes_constants import get_hermes_home
from qrcode import QRCode
from qrcode.constants import ERROR_CORRECT_M

QR_PNG = os.path.expanduser("~/Desktop/wechat_qr.png")


def generate_and_open_qr(scan_data: str):
    """Generate a QR PNG and open it. Also print ASCII as fallback."""
    # PNG (scannable by WeChat camera)
    qr = QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(scan_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(QR_PNG)

    # Open on macOS
    if sys.platform == "darwin":
        os.system(f"open {QR_PNG}")

    # ASCII fallback
    qr_ascii = QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=1, border=2)
    qr_ascii.add_data(scan_data)
    qr_ascii.make(fit=True)
    qr_ascii.print_ascii(invert=True)


async def main():
    import aiohttp
    hermes_home = get_hermes_home()

    print("=" * 60)
    print("  Hermes × 微信 扫码登录")
    print("=" * 60)

    async with aiohttp.ClientSession(
        trust_env=True, connector=_make_ssl_connector()
    ) as session:

        deadline = time.monotonic() + 300
        refresh_count = 0

        while time.monotonic() < deadline and refresh_count <= 3:
            # Step 1: Fetch QR data
            try:
                qr_resp = await _api_get(
                    session,
                    base_url=ILINK_BASE_URL,
                    endpoint=f"{EP_GET_BOT_QR}?bot_type=3",
                    timeout_ms=35000,
                )
            except Exception as exc:
                print(f"\n❌ 获取二维码失败: {exc}")
                return 1

            qrcode_value = str(qr_resp.get("qrcode") or "")
            liteapp_url = str(qr_resp.get("qrcode_img_content") or "")
            scan_data = liteapp_url if liteapp_url else qrcode_value

            if not qrcode_value:
                print("❌ 未收到二维码数据")
                return 1

            # Step 2: Generate and open QR image
            generate_and_open_qr(scan_data)

            print()
            print("━" * 60)
            print(f"  📱 二维码图片已打开: {QR_PNG}")
            print(f"  🔗 备用链接: {scan_data}")
            print("━" * 60)
            print()
            print("  等待扫码", end="", flush=True)

            # Step 3: Poll for scan + confirm
            current_base_url = ILINK_BASE_URL
            qr_deadline = min(time.monotonic() + 120, deadline)
            result = {"action": "timeout"}

            while time.monotonic() < qr_deadline:
                try:
                    status_resp = await _api_get(
                        session,
                        base_url=current_base_url,
                        endpoint=f"{EP_GET_QR_STATUS}?qrcode={qrcode_value}",
                        timeout_ms=35000,
                    )
                except asyncio.TimeoutError:
                    await asyncio.sleep(1)
                    continue
                except Exception:
                    await asyncio.sleep(1)
                    continue

                status = str(status_resp.get("status") or "wait")

                if status == "wait":
                    print(".", end="", flush=True)
                elif status == "scaned":
                    print("\n  📱 已扫码，请在微信里点「确认登录」！")
                elif status == "scaned_but_redirect":
                    rh = str(status_resp.get("redirect_host") or "")
                    if rh:
                        current_base_url = f"https://{rh}"
                elif status == "expired":
                    result = {"action": "refresh"}
                    break
                elif status == "confirmed":
                    result = {
                        "action": "done",
                        "account_id": str(status_resp.get("ilink_bot_id") or ""),
                        "token": str(status_resp.get("bot_token") or ""),
                        "base_url": str(status_resp.get("baseurl") or ILINK_BASE_URL),
                        "user_id": str(status_resp.get("ilink_user_id") or ""),
                    }
                    break

                await asyncio.sleep(1)

            # Step 4: Handle result
            if result["action"] == "done":
                account_id = result["account_id"]
                token = result["token"]
                base_url = result["base_url"]

                if not account_id or not token:
                    print("\n❌ 凭证不完整")
                    return 1

                # Save credentials
                save_weixin_account(
                    hermes_home, account_id=account_id, token=token,
                    base_url=base_url, user_id=result.get("user_id", ""),
                )

                print(f"\n\n✅ 微信登录成功！Bot ID: {account_id}")

                # Write to .env
                env_path = os.path.join(hermes_home, ".env")
                lines = []
                if os.path.exists(env_path):
                    with open(env_path) as f:
                        lines = [l for l in f.read().splitlines()
                                 if not l.startswith("WEIXIN_")]
                user_id = result.get("user_id", "")
                lines.append(f"WEIXIN_ACCOUNT_ID={account_id}")
                lines.append(f"WEIXIN_TOKEN={token}")
                if base_url != ILINK_BASE_URL:
                    lines.append(f"WEIXIN_BASE_URL={base_url}")
                # ⚠️ REQUIRED: without DM_POLICY=open, ALL messages return "Unauthorized"
                lines.append("WEIXIN_DM_POLICY=open")
                if user_id:
                    lines.append(f"WEIXIN_ALLOWED_USERS={user_id}")
                lines.append("")
                with open(env_path, "w") as f:
                    f.write("\n".join(lines))

                print(f"✅ 环境变量已写入 {env_path}")
                print()
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("  下一步：hermes gateway start")
                print("  然后微信里发消息，AI 就会回复！")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                return 0

            elif result["action"] == "refresh":
                refresh_count += 1
                print(f"\n⏳ 二维码过期，刷新 ({refresh_count}/3)...\n")

        print(f"\n❌ 超时或刷新次数过多")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
