# 🚀 Twitter Account Checker

A **blazing fast**, **modern**, and **async-powered** Twitter account checker that validates accounts using `auth_token` (and `ct0` if available).  
Built for speed, reliability, and ease of use.

---

## ✨ Features

- **⚡ High-Speed Checking** – Asynchronous requests with `httpx` for maximum CPM.
- **🔎 Flexible Input** – Works with any account format, auto-extracting tokens via regex.
- **🛡 Optional ct0 Support** – Uses `ct0` when present, otherwise falls back to `auth_token` only.
- **🎨 Colorful & Clean CLI** – Beautiful output with CPM stats, skips invalid tokens automatically.
- **🌐 Proxy Support** – Single proxy configuration for all requests.
- **🧵 Multi-threading** – Adjustable thread count from config.
- **📂 Organized Output** – Results saved into categorized files:
  - `output/unlocked.txt` (Valid accounts)
  - `output/locked.txt` (Locked accounts)
  - `output/suspended.txt` (Suspended accounts)
  - `output/badToken.txt` (Invalid tokens)

---

python main.py 
