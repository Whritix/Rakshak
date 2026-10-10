"""Capture UI Screenshot in 100% Air-Gapped / Offline Environment.

Launches Microsoft Edge in headless mode via DevTools Protocol (CDP):
1. Intercepts and logs all network requests to verify ZERO external calls.
2. Injects tactical operator session.
3. Renders the Joint COP interactive map with synthetic basemap and GeoJSON overlay.
4. Takes screenshot and writes to scratch/ and artifact directory.
"""
import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
import websockets
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUTPUT_DIR = Path("scratch")
ARTIFACT_DIR = Path(r"C:\Users\awhri\.gemini\antigravity\brain\c612c78c-a3a4-4026-b0d3-ba0bc49c43e7")

async def run_capture():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_profile = tempfile.mkdtemp(prefix="edge_airgap_")
    port = 9333

    print("[1] Obtaining tactical operator token from local backend...", flush=True)
    login_body = json.dumps({
        "username": "tactical_smoke_1791139880",
        "password": "DefenseSecurePassword!2026"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=login_body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        auth_data = json.loads(resp.read().decode())
    token = auth_data["access_token"]
    user_json = json.dumps(auth_data["user"])
    print(f"    Operator authenticated: {auth_data['user']['full_name']} ({auth_data['user']['callsign']})", flush=True)

    print("[2] Spawning headless Edge with CDP remote debugging...", flush=True)
    proc = subprocess.Popen([
        EDGE_EXE,
        "--headless=new",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={temp_profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1600,1000",
        "--hide-scrollbars",
        "--disable-gpu",
        "about:blank"
    ])

    try:
        ws_url = None
        for _ in range(40):
            await asyncio.sleep(0.3)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list") as r:
                    tabs = json.loads(r.read().decode())
                    for tab in tabs:
                        if tab.get("type") == "page" and tab.get("webSocketDebuggerUrl"):
                            ws_url = tab.get("webSocketDebuggerUrl")
                            break
                    if ws_url:
                        break
            except Exception:
                pass

        if not ws_url:
            raise RuntimeError("Could not find WebSocket URL for Edge page")

        print(f"    CDP URL: {ws_url}", flush=True)

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            msg_counter = 0
            pending_commands = {}
            captured_requests = []
            external_violations = []

            async def send_cmd(method: str, params: dict = None):
                nonlocal msg_counter
                msg_counter += 1
                fut = asyncio.get_event_loop().create_future()
                pending_commands[msg_counter] = fut
                msg = {"id": msg_counter, "method": method, "params": params or {}}
                await ws.send(json.dumps(msg))
                return await fut

            async def listen_loop():
                try:
                    async for raw in ws:
                        evt = json.loads(raw)
                        cid = evt.get("id")
                        if cid in pending_commands:
                            fut = pending_commands.pop(cid)
                            if "error" in evt:
                                fut.set_exception(RuntimeError(evt["error"]))
                            else:
                                fut.set_result(evt.get("result", {}))
                        elif "method" in evt:
                            m = evt["method"]
                            if m == "Network.requestWillBeSent":
                                url = evt["params"]["request"]["url"]
                                captured_requests.append(url)
                                if not (url.startswith("http://127.0.0.1") or url.startswith("http://localhost") or url.startswith("data:") or url.startswith("blob:")):
                                    external_violations.append(url)
                except asyncio.CancelledError:
                    pass

            listener_task = asyncio.create_task(listen_loop())

            try:
                await send_cmd("Network.enable")
                await send_cmd("Page.enable")
                await send_cmd("Runtime.enable")

                print(f"[3] Navigating to {BASE_URL}...", flush=True)
                await send_cmd("Page.navigate", {"url": f"{BASE_URL}/"})
                await asyncio.sleep(2.0)

                print("[4] Injecting authentication session...", flush=True)
                injection_js = f"""
                (() => {{
                    sessionStorage.setItem('rakshak_token', {json.dumps(token)});
                    sessionStorage.setItem('rakshak_user', {json.dumps(user_json)});
                    window.location.reload();
                }})()
                """
                await send_cmd("Runtime.evaluate", {"expression": injection_js})
                print("[5] Waiting for map tiles, vectors, and tactical layers to stabilize...", flush=True)
                await asyncio.sleep(4.0)

                print("[6] Capturing screenshot via Page.captureScreenshot...", flush=True)
                result = await send_cmd("Page.captureScreenshot", {"format": "png"})
                img_data = base64.b64decode(result["data"])

                dest1 = OUTPUT_DIR / "offline_map_screenshot.png"
                dest1.write_bytes(img_data)
                print(f"    Saved screenshot to {dest1} ({len(img_data):,} bytes)", flush=True)

                if ARTIFACT_DIR.exists():
                    dest2 = ARTIFACT_DIR / "offline_map_screenshot.png"
                    dest2.write_bytes(img_data)
                    print(f"    Saved artifact screenshot to {dest2}", flush=True)

                # Capture Theater Overview at Zoom 4
                print("[6b] Zooming out to Zoom 4 (Theater Overview)...", flush=True)
                await send_cmd("Runtime.evaluate", {"expression": "document.querySelector('.leaflet-control-zoom-out')?.click();"})
                await asyncio.sleep(0.6)
                await send_cmd("Runtime.evaluate", {"expression": "document.querySelector('.leaflet-control-zoom-out')?.click();"})
                await asyncio.sleep(2.0)
                res_z4 = await send_cmd("Page.captureScreenshot", {"format": "png"})
                img_z4 = base64.b64decode(res_z4["data"])
                dest_z4 = OUTPUT_DIR / "offline_map_zoom4.png"
                dest_z4.write_bytes(img_z4)
                print(f"    Saved zoom 4 screenshot to {dest_z4} ({len(img_z4):,} bytes)", flush=True)
                if ARTIFACT_DIR.exists():
                    (ARTIFACT_DIR / "offline_map_zoom4.png").write_bytes(img_z4)

                print("\n[7] ZERO-EGRESS AIR-GAP NETWORK AUDIT:", flush=True)
                print(f"    Total requests captured: {len(captured_requests)}", flush=True)
                tile_reqs = [u for u in captured_requests if "/api/tiles/" in u]
                print(f"    Offline synthetic tile requests: {len(tile_reqs)}", flush=True)
                for t in tile_reqs[:6]:
                    print(f"      - {t}", flush=True)
                if len(tile_reqs) > 6:
                    print(f"      ... and {len(tile_reqs) - 6} more local tile requests", flush=True)

                print(f"    External violations: {len(external_violations)}", flush=True)
                if external_violations:
                    for v in external_violations:
                        print(f"      [VIOLATION] {v}", flush=True)
                    raise AssertionError("External network calls detected in air-gapped session!")
                else:
                    print("    VERIFIED: Zero external requests. 100% air-gapped sovereign node.", flush=True)

            finally:
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass

    finally:
        print("[8] Terminating browser process...", flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(temp_profile, ignore_errors=True)
        print("Done.", flush=True)

if __name__ == "__main__":
    asyncio.run(run_capture())
