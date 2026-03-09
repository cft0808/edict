import time, pathlib, subprocess, sys
base = pathlib.Path(r"C:\Users\0x00\edict")
while True:
    for name in ["sync_from_openclaw_runtime.py","sync_agent_config.py","apply_model_changes.py","sync_officials_stats.py","refresh_live_data.py"]:
        try:
            subprocess.run([sys.executable, str(base / 'scripts' / name)], cwd=str(base), timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    time.sleep(15)
