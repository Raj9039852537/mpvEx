import os
import time
import requests
from pathlib import Path

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

ARTIFACTS_PATH = Path("artifacts")
ABIS = ["arm64-v8a"]

# ---------- helpers ----------

def find_apk():
    for d in ARTIFACTS_PATH.glob("*"):
        if d.is_dir():
            for apk in d.glob("*.apk"):
                return apk
    raise FileNotFoundError("No APK found")

def normalize(text: str) -> str:
    return (text or "").replace("\\n", "\n")

def commit_info():
    return (
        (os.environ.get("COMMIT_ID") or "unknown")[:7],
        os.environ.get("COMMIT_URL") or "",
        os.environ.get("COMMIT_MESSAGE") or "unknown",
    )

def caption():
    commit_id, commit_url, commit_msg = commit_info()
    ai = normalize(os.environ.get("AI_SUMMARY", ""))

    text = (
        "Test version.\n\n"
        "Commit Message:\n"
        f"<blockquote expandable>{commit_msg}</blockquote>\n\n"
        f"See commit details "
        f'<a href="{commit_url}">{commit_id}</a>'
    )

    if ai and len(text) + len(ai) < 1024:
        text += f"\n\n<blockquote expandable>{ai}</blockquote>"

    return text[:1024]

def metadata():
    return (
        f"<code>{os.environ.get('BUILD_TIMESTAMP','')}</code> "
        f"<code>{(os.environ.get('COMMIT_ID','')[:7])}</code>\n"
        f"<code>{os.environ.get('COMMIT_MESSAGE','')}</code>"
    )

# ---------- telegram ----------

def send_document(chat_id, path: Path, caption_text: str):
    with path.open("rb") as f:
        r = requests.post(
            f"{API_URL}/sendDocument",
            data={
                "chat_id": chat_id,
                "caption": caption_text,
                "parse_mode": "HTML",
            },
            files={"document": f},
            timeout=600,
        )
    r.raise_for_status()

def send_message(chat_id, text: str):
    r = requests.post(
        f"{API_URL}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=60,
    )
    r.raise_for_status()

# ---------- main ----------

def main():
    apk = find_apk()

    for _ in range(3):  # retry
        try:
            send_document(CHAT_ID, apk, caption())
            send_message(CHAT_ID, metadata())
            break
        except Exception as e:
            print("Retry sendDocument:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
