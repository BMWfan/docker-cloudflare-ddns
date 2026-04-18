import unittest
from unittest.mock import MagicMock, patch

import update_dns


class UpdateDnsTests(unittest.TestCase):
    @patch("update_dns.cf_request")
    def test_update_record_updates_existing_record(self, cf_request):
        response = MagicMock()
        response.json.return_value = {
            "result": [{"id": "record-1", "content": "2001:db8::1"}]
        }
        cf_request.side_effect = [response, None]

        update_dns.ZONE_ID = "zone-1"
        update_dns.update_record_for_host("host.example.com", "2001:db8::2")

        self.assertEqual(cf_request.call_count, 2)
        cf_request.assert_any_call(
            "PUT",
            "https://api.cloudflare.com/client/v4/zones/zone-1/dns_records/record-1",
            json={
                "type": "AAAA",
                "name": "host.example.com",
                "content": "2001:db8::2",
                "ttl": 1,
                "proxied": False,
            },
        )

    @patch("update_dns.cf_request")
    def test_update_record_creates_missing_record(self, cf_request):
        response = MagicMock()
        response.json.return_value = {"result": []}
        cf_request.side_effect = [response, None]

        update_dns.ZONE_ID = "zone-1"
        update_dns.update_record_for_host("host.example.com", "2001:db8::2")

        self.assertEqual(cf_request.call_count, 2)
        cf_request.assert_any_call(
            "POST",
            "https://api.cloudflare.com/client/v4/zones/zone-1/dns_records",
            json={
                "type": "AAAA",
                "name": "host.example.com",
                "content": "2001:db8::2",
                "ttl": 1,
                "proxied": False,
            },
        )

    @patch("update_dns.docker.from_env")
    def test_collect_all_hosts_merges_env_and_container_hosts(self, from_env):
        update_dns.STATIC_HOSTS = "static.example.com, second.example.com"

        container = MagicMock()
        container.labels = {"cloudflare.dns": "label.example.com"}
        container.attrs = {
            "Config": {"Env": ["CLOUDFLARE_HOST=env.example.com", "OTHER=value"]}
        }

        second_container = MagicMock()
        second_container.labels = {}
        second_container.attrs = {"Config": {"Env": ["CLOUDFLARE_HOST=env-only.example.com"]}}

        docker_client = MagicMock()
        docker_client.containers.list.return_value = [container, second_container]
        from_env.return_value = docker_client

        hosts = update_dns.collect_all_hosts()

        self.assertEqual(
            hosts,
            [
                "env-only.example.com",
                "label.example.com",
                "second.example.com",
                "static.example.com",
            ],
        )


if __name__ == "__main__":
    unittest.main()
