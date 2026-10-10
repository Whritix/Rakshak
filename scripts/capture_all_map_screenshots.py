"""Capture All Four Maps and All Three Basemap Styles in 100% Air-Gapped Environment.

Zero external network calls (monitored via CDP).
Saves screenshots to evaluation/results/map_screenshots/:
  1. map_1_joint_cop.png
  2. map_2_naval_domain.png
  3. map_3_army_domain.png
  4. map_4_mission_planner.png
  5. style_1_offline_basemap.png
  6. style_2_dark_tactical.png
  7. style_3_offline_terrain.png
"""
import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
import websockets

BASE_URL = "http://127.0.0.1:8000"
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUTPUT_DIR = Path("evaluation/results/map_screenshots")

async def capture_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_profile = tempfile.mkdtemp(prefix="edge_airgap_maps_")
    port = 9338

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
        "--window-size=1600,1050",
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
                await asyncio.sleep(4.5)

                async def save_screenshot(name: str):
                    res = await send_cmd("Page.captureScreenshot", {"format": "png"})
                    img_bytes = base64.b64decode(res["data"])
                    dest = OUTPUT_DIR / f"{name}.png"
                    dest.write_bytes(img_bytes)
                    print(f"    [+] Saved {dest.name} ({len(img_bytes):,} bytes)", flush=True)

                # 1. Map 1: Joint COP Map (Default: Offline basemap + Coastline/EEZ overlay)
                print("\n[6a] Capturing Map 1: Joint COP Map...", flush=True)
                await asyncio.sleep(1.0)
                await save_screenshot("map_1_joint_cop")

                # 2. Style 2: Dark tactical (synthetic)
                print("\n[6b] Switching to Style 2: Dark tactical (synthetic)...", flush=True)
                click_dark = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('.map-wrap button')).find(b => b.innerText.includes('Dark tactical'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
                """
                await send_cmd("Runtime.evaluate", {"expression": click_dark})
                await asyncio.sleep(2.5)
                await save_screenshot("style_2_dark_tactical")

                # 3. Style 3: Offline terrain (synthetic)
                print("\n[6c] Switching to Style 3: Offline terrain (synthetic)...", flush=True)
                click_terrain = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('.map-wrap button')).find(b => b.innerText.includes('Offline terrain'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
                """
                await send_cmd("Runtime.evaluate", {"expression": click_terrain})
                await asyncio.sleep(2.5)
                await save_screenshot("style_3_offline_terrain")

                # 4. Style 1: Offline basemap (synthetic)
                print("\n[6d] Switching back to Style 1: Offline basemap (synthetic)...", flush=True)
                click_basemap = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('.map-wrap button')).find(b => b.innerText.includes('Offline basemap'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
                """
                await send_cmd("Runtime.evaluate", {"expression": click_basemap})
                await asyncio.sleep(2.5)
                await save_screenshot("style_1_offline_basemap")

                # 5. Map 2: Naval Domain Map
                print("\n[6e] Navigating to Naval Domain...", flush=True)
                nav_naval = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('nav button')).find(b => b.innerText.includes('Naval Domain'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
                """
                await send_cmd("Runtime.evaluate", {"expression": nav_naval})
                await asyncio.sleep(3.0)
                await save_screenshot("map_2_naval_domain")

                # 6. Map 3: Army Domain Map
                print("\n[6f] Navigating to Army Domain...", flush=True)
                nav_army = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('nav button')).find(b => b.innerText.includes('Army Domain'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
                """
                await send_cmd("Runtime.evaluate", {"expression": nav_army})
                await asyncio.sleep(3.0)
                await save_screenshot("map_3_army_domain")

                # 7. Map 4: Mission Planner Map
                print("\n[6g] Navigating to Mission Planner...", flush=True)
                nav_mission = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('nav button')).find(b => b.innerText.includes('Mission Planner'));
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
                """
                await send_cmd("Runtime.evaluate", {"expression": nav_mission})
                await asyncio.sleep(3.5)
                await save_screenshot("map_4_mission_planner")

                print("\n[7] ZERO-EGRESS AIR-GAP NETWORK AUDIT:", flush=True)
                print(f"    Total requests captured: {len(captured_requests)}", flush=True)
                tile_reqs = [u for u in captured_requests if "/api/tiles/" in u]
                print(f"    Offline procedural tile requests: {len(tile_reqs)}", flush=True)
                for t in tile_reqs[:6]:
                    print(f"      - {t}", flush=True)
                if len(tile_reqs) > 6:
                    print(f"      ... and {len(tile_reqs) - 6} more local tile requests", flush=True)

                print(f"    External network violations: {len(external_violations)}", flush=True)
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
    asyncio.run(capture_all())
