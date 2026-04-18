from flask import Flask
import threading
import subprocess
import sys
import event_listener

app = Flask(__name__)
update_lock = threading.Lock()

def run_updater():
    if not update_lock.acquire(blocking=False):
        print("⏳ DNS-Updater läuft bereits, überspringe weiteren Trigger")
        return

    print("🔁 Starte DNS-Updater...")
    try:
        subprocess.run([sys.executable, "/app/update_dns.py"], check=False)
    finally:
        update_lock.release()

@app.route("/ip-change")
def ip_change():
    threading.Thread(target=run_updater, daemon=True).start()
    return "OK", 200

if __name__ == "__main__":
    print("🔁 Initiale DNS-Aktualisierung beim Containerstart...")
    run_updater()

    print("📡 Starte Docker-Event-Listener...")
    threading.Thread(target=event_listener.listen_for_docker_events, daemon=True).start()

    app.run(host="0.0.0.0", port=5055)
