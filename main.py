import httpx
import asyncio
import aiofiles
import re
import json
import os
import time
from colorama import Fore, Style, init

init(autoreset=True)

# --- Regex for tokens ---
AUTH_TOKEN_REGEX = re.compile(r'[a-fA-F0-9]{40}')
CT0_REGEX = re.compile(r'[a-fA-F0-9]{64,128}')

# Error codes mapping
ERROR_CODES = {
    32: "BAD_TOKEN",
    64: "SUSPENDED",
    141: "SUSPENDED",
    326: "LOCKED",
    353: "LOCKED"
}

OUTPUT_FILES = {
    "good": "output/unlocked.txt",
    "locked": "output/locked.txt",
    "suspended": "output/suspended.txt",
    "bad": "output/badToken.txt"
}

os.makedirs("output", exist_ok=True)

# Load config (proxy + threads)
with open("config.json", "r") as cf:
    CONFIG = json.load(cf)
PROXY = CONFIG.get("proxy", None)
THREAD_LIMIT = CONFIG.get("threads", 20)

# --- Counters ---
start_time = time.time()
checked_count = 0

h = r"""
  __             __            __                        
_/  |___  _  ___/  |_  _______/  |_  ___________   ____  
\   __\ \/ \/ /\   __\/  ___/\   __\/  _ \_  __ \_/ __ \ 
 |  |  \     /  |  |  \___ \  |  | (  <_> )  | \/\  ___/ 
 |__|   \/\_/   |__| /____  > |__|  \____/|__|    \___  >
                          \/                          \/ 
"""

def banner(line_count):
    print(h)
    print(Fore.YELLOW + Style.BRIGHT + "-" * 60)
    print(Fore.GREEN + Style.BRIGHT + "   https://twtstore.com → Buy high quality Twitter accounts @ $0.02 each")
    print(Fore.YELLOW + Style.BRIGHT + "-" * 60)
    print(Fore.GREEN + Style.BRIGHT + "  Join our Telegram for help → https://t.me/twttools")
    print(Fore.YELLOW + Style.BRIGHT + "-" * 60)
    print(Fore.CYAN + Style.BRIGHT + f" Accounts to check: {line_count}")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60 + "\n" + Style.RESET_ALL)


async def write_to_file(path, line):
    async with aiofiles.open(path, "a", encoding="utf-8") as f:
        await f.write(line.strip() + "\n")


def extract_tokens(line: str):
    auth_token_match = AUTH_TOKEN_REGEX.search(line)
    ct0_match = CT0_REGEX.search(line)
    auth_token = auth_token_match.group(0) if auth_token_match else None
    ct0 = ct0_match.group(0) if ct0_match else None
    return auth_token, ct0


async def check_account(client, line: str):
    global checked_count
    auth_token, ct0 = extract_tokens(line)

    if not auth_token:
        print(Fore.YELLOW + f"[SKIP] No valid auth_token -> {line.strip()}")
        return

    headers = {
        "Origin": "https://twitter.com",
        "Referer": "https://twitter.com/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        ),
        "timezone": "America/Anchorage",
        "sec-ch-ua": '"Google Chrome";v="138", "Chromium";v="138", "Not/A)Brand";v="24"',
        "accept-language": "en-US,en;q=0.9",
        "x-twitter-client-language": "en",
        "x-twitter-active-user": "yes",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "cookie": f"auth_token={auth_token}" + (f"; ct0={ct0}" if ct0 else "")
    }

    if ct0:
        headers["x-csrf-token"] = ct0  # only add ct0 header if present

    url = "https://api.twitter.com/1.1/live_pipeline/update_subscriptions"

    for attempt in range(3):
        try:
            res = await client.post(url, headers=headers)
            break
        except Exception as e:
            print(Fore.RED + f"[ERROR] {auth_token[:6]} attempt {attempt+1}/3 -> {e}")
            await asyncio.sleep(2)
    else:
        print(Fore.RED + f"[FAIL] {auth_token}")
        return

    checked_count += 1
    elapsed = max(1, time.time() - start_time)
    cpm = (checked_count / elapsed) * 60

    if res.status_code == 400:
        await write_to_file(OUTPUT_FILES["good"], line)
        print(Fore.GREEN + f"[GOOD] {auth_token} | CPM: {cpm:.0f}")
        return

    try:
        data = res.json()
    except Exception:
        print(Fore.RED + f"[INVALID JSON] {auth_token}")
        return

    code = None
    if "errors" in data and isinstance(data["errors"], list) and len(data["errors"]) > 0:
        code = data["errors"][0].get("code")

    status = ERROR_CODES.get(code, "UNKNOWN")
    if status == "LOCKED":
        await write_to_file(OUTPUT_FILES["locked"], line)
    elif status == "SUSPENDED":
        await write_to_file(OUTPUT_FILES["suspended"], line)
    elif status == "BAD_TOKEN":
        await write_to_file(OUTPUT_FILES["bad"], line)

    print(Fore.CYAN + f"[{status}] {auth_token} | CPM: {cpm:.0f}")


async def main():
    async with aiofiles.open("accounts.txt", "r", encoding="utf-8") as f:
        lines = await f.readlines()

    banner(len(lines))
    input(Fore.YELLOW + "Press ENTER to start checking...")

    limits = asyncio.Semaphore(THREAD_LIMIT)
    async with httpx.AsyncClient(timeout=15, proxies=PROXY) as client:
        async def limited_check(line):
            async with limits:
                await check_account(client, line)

        tasks = [limited_check(line) for line in lines if line.strip()]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
