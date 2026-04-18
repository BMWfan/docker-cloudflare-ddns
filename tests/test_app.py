import unittest
from unittest.mock import patch

import app


class AppRouteTests(unittest.TestCase):
    @patch("app.threading.Thread")
    def test_ip_change_starts_background_thread(self, thread_cls):
        client = app.app.test_client()

        response = client.get("/ip-change")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"OK")
        thread_cls.assert_called_once_with(target=app.run_updater, daemon=True)
        thread_cls.return_value.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
