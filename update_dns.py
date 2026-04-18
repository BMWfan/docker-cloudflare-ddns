import os
import sys
import time

import docker
import requests


CLOUDFLARE_API_TOKEN = os.getenv("CF_API_TOKEN")
ZONE_ID = os.getenv("CF_ZONE_ID")
STATIC_HOSTS = os.getenv("STATIC_HOSTS", "")

HEADERS = {
    "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    "Content-Type": "application/json",
}

LOCK_FILE = "/tmp/dns_update.lock"


def acquire_lock():
    if os.path.exists(LOCK_FILE):
        print("DNS update is already running - skipping")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def get_ipv6(retries=5, delay=2):
    urls = [
        "https://api64.ipify.org",
        "https://ifconfig.co/ip",
        "https://ipv6.icanhazip.com",
    ]

    last_error = None

    for attempt in range(1, retries + 1):
        for url in urls:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                ip = response.text.strip()

                if ":" not in ip:
                    raise ValueError(f"Did not receive an IPv6 address: {ip}")

                return ip

            except Exception as e:
                last_error = e

        print(f"IPv6 lookup failed ({attempt}/{retries}) -> {last_error}")
        time.sleep(delay)

    raise RuntimeError("Could not determine public IPv6 address")


def cf_request(method, url, json=None, retries=5, delay=2):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=HEADERS,
                json=json,
                timeout=10,
            )

            if 400 <= response.status_code < 500 and response.status_code != 429:
                print(f"Cloudflare API error {response.status_code}: {response.text}")
                response.raise_for_status()

            response.raise_for_status()
            return response

        except requests.RequestException as e:
            last_error = e
            print(f"Cloudflare API request failed ({attempt}/{retries}) -> {e}")
            time.sleep(delay)

    raise RuntimeError(f"Cloudflare API is unreachable: {last_error}")


def update_record_for_host(host, ipv6):
    if ":" not in ipv6:
        print(f"Skipping {host}: invalid IPv6 address ({ipv6})")
        return

    list_url = (
        f"https://api.cloudflare.com/client/v4/zones/"
        f"{ZONE_ID}/dns_records?type=AAAA&name={host}"
    )

    response = cf_request("GET", list_url)
    records = response.json().get("result", [])

    if records:
        record = records[0]
        record_id = record["id"]

        if record["content"] == ipv6:
            print(f"IP unchanged for {host}")
            return

        print(f"Updating {host} -> {ipv6}")

        update_url = (
            f"https://api.cloudflare.com/client/v4/zones/"
            f"{ZONE_ID}/dns_records/{record_id}"
        )

        payload = {
            "type": "AAAA",
            "name": host,
            "content": ipv6,
            "ttl": 1,
            "proxied": False,
        }

        cf_request("PUT", update_url, json=payload)
        print(f"Updated: {host}")

    else:
        print(f"Creating DNS record: {host} -> {ipv6}")

        create_url = (
            f"https://api.cloudflare.com/client/v4/zones/"
            f"{ZONE_ID}/dns_records"
        )

        payload = {
            "type": "AAAA",
            "name": host,
            "content": ipv6,
            "ttl": 1,
            "proxied": False,
        }

        cf_request("POST", create_url, json=payload)
        print(f"Created: {host}")


def collect_all_hosts():
    hosts = set()

    for host in [h.strip() for h in STATIC_HOSTS.split(",") if h.strip()]:
        hosts.add(host)

    docker_client = docker.from_env()

    for container in docker_client.containers.list():
        labels = container.labels or {}
        env_vars = container.attrs["Config"].get("Env", [])
        env_dict = dict(e.split("=", 1) for e in env_vars if "=" in e)

        host = labels.get("cloudflare.dns")
        if not host:
            host = env_dict.get("CLOUDFLARE_HOST")

        if host:
            hosts.add(host)

    return sorted(hosts)


def update_all_hosts():
    ipv6 = get_ipv6()
    hosts = collect_all_hosts()

    if not hosts:
        print("No hosts found")
        return

    for host in hosts:
        update_record_for_host(host, ipv6)


if __name__ == "__main__":
    acquire_lock()
    try:
        if len(sys.argv) > 1:
            target_host = sys.argv[1].strip()
            if target_host:
                ipv6 = get_ipv6()
                update_record_for_host(target_host, ipv6)
        else:
            update_all_hosts()
    finally:
        release_lock()
