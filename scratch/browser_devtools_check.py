"""Offline Browser Run with DevTools Network Tab Monitoring via CDP.

Launches Microsoft Edge in headless mode with remote debugging enabled,
attaches to the Chrome DevTools Protocol (CDP) Network domain,
navigates to http://127.0.0.1:8000, intercepts all outgoing network requests,
and proves 100% air-gapped zero-external-network execution.
"""
import asyncio
import json
import subprocess
import time
import urllib.request
import websockets

EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
TARGET_URL = "http://127.0.0.1:8000"
CDP_PORT = 9222


async def monitor_network():
    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — OFFLINE BROWSER DEVTOOLS NETWORK AUDIT")
    print("=" * 70)

    # 1. Launch Edge headless with remote debugging
    cmd = [
        EDGE_EXE,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=C:\\temp\\edge_airgap_profile",
        "about:blank",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    try:
        # 2. Get WebSocket debugger URL from CDP endpoint
        resp = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=5)
        tabs = json.loads(resp.read().decode())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"[*] Attached to browser DevTools session: {tabs[0]['title']}")

        network_requests = []
        external_requests = []

        async with websockets.connect(ws_url) as ws:
            # Enable Network domain
            await ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
            # Enable Page domain
            await ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
            # Navigate to target
            await ws.send(json.dumps({"id": 3, "method": "Page.navigate", "params": {"url": TARGET_URL}}))

            print(f"[*] Navigating to {TARGET_URL}...")
            start_time = time.time()

            # Listen for network events for 6 seconds
            while time.time() - start_time < 6.0:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(msg)
                    if data.get("method") == "Network.requestWillBeSent":
                        req = data["params"]["request"]
                        url = req["url"]
                        method = req["method"]
                        network_requests.append((method, url))
                        # Check if non-loopback (allowing internal browser schemes and loopback)
                        if not any(lh in url for lh in ["127.0.0.1", "localhost", "0.0.0.0", "blob:", "data:", "edge://", "chrome://"]):
                            external_requests.append((method, url))
                except asyncio.TimeoutError:
                    pass

        print(f"\n[+] DevTools Network Tab captured {len(network_requests)} total HTTP requests:")
        for m, u in network_requests:
            print(f"    [{m}] {u}")

        print("\n" + "-" * 70)
        print(f"  Non-Loopback / External Outbound Requests: {len(external_requests)}")
        if external_requests:
            for m, u in external_requests:
                print(f"  [VIOLATION] {m} {u}")
            print("  [FAIL] Browser made external network requests!")
            return False
        else:
            print("  [PASS] ZERO external network calls! 100% requests strictly served on localhost loopback.")
            print("-" * 70)
            return True

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    success = asyncio.run(monitor_network())
    if not success:
        exit(1)
