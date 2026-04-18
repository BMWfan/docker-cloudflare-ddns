from flask import Flask
import threading
import subprocess
import sys
import event_listener

app = Flask(__name__)
update_lock = threading.Lock()

def run_updater():
    if not update_lock.acquire(blocking=False):
        print("DNS updater is already running, skipping duplicate trigger")
        return

    print("Starting DNS updater...")
    try:
        subprocess.run([sys.executable, "/app/update_dns.py"], check=False)
    finally:
        update_lock.release()

@app.route("/ip-change")
def ip_change():
    threading.Thread(target=run_updater, daemon=True).start()
    return "OK", 200

if __name__ == "__main__":
    print("Running initial DNS update on container startup...")
    run_updater()

    print("Starting Docker event listener...")
    threading.Thread(target=event_listener.listen_for_docker_events, daemon=True).start()

    app.run(host="0.0.0.0", port=5055)
