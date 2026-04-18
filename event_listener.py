import docker
import subprocess
import time
import sys

def listen_for_docker_events():
    print("📡 Starte Docker-Event-Listener...")

    while True:
        try:
            api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
            container_client = docker.from_env()

            for event in api_client.events(decode=True):
                if event.get("Type") != "container":
                    continue

                action = event.get("Action")
                if action != "start":
                    continue

                container_name = event.get("Actor", {}).get("Attributes", {}).get("name", "unbekannt")
                container_id = event.get("id") or event.get("Actor", {}).get("ID")

                if container_name == "cloudflare-updater":
                    continue

                if not container_id:
                    print(f"⚠️ Keine Container-ID für '{container_name}' gefunden")
                    continue

                try:
                    container = container_client.containers.get(container_id)

                    labels = container.labels or {}
                    env_vars = container.attrs["Config"].get("Env", [])
                    env_dict = dict(e.split("=", 1) for e in env_vars if "=" in e)

                    cloudflare_host = labels.get("cloudflare.dns")
                    if not cloudflare_host:
                        cloudflare_host = env_dict.get("CLOUDFLARE_HOST")

                    if cloudflare_host:
                        print(f"🌐 Trigger für '{container_name}' → {cloudflare_host}")
                        subprocess.run(
                            [sys.executable, "/app/update_dns.py", cloudflare_host],
                            check=False,
                        )

                except Exception as e:
                    print(f"❌ Fehler bei '{container_name}': {e}")

        except Exception as e:
            print(f"💥 Schwerer Fehler im Listener: {e}")
            time.sleep(5)
