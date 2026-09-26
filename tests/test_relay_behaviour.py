import json, socket, tempfile, unittest
from pathlib import Path

from relay.http_client import RelayError, build_url, parse_key_value_lines, perform_request, pretty_body, to_curl
from relay.mock_server import MockResponse, MockServer
from relay.models import RequestSpec
from relay.storage import RelayStore


class ParsingTests(unittest.TestCase):
    def test_comments_and_blank_lines_are_skipped(self):
        self.assertEqual(parse_key_value_lines('# note\n\n  page = 2  \n'), {'page': '2'})

    def test_equals_before_colon_is_a_param_with_a_colon_in_its_value(self):
        self.assertEqual(parse_key_value_lines('redirect=https://example.com/cb\ntime=10:30'),
                         {'redirect': 'https://example.com/cb', 'time': '10:30'})

    def test_colon_before_equals_is_a_header_with_equals_in_its_value(self):
        self.assertEqual(parse_key_value_lines('Authorization: Bearer abc=='), {'Authorization': 'Bearer abc=='})

    def test_malformed_lines_are_rejected(self):
        for bad in ('no separator', ': value', '=value'):
            with self.subTest(bad=bad), self.assertRaises(RelayError):
                parse_key_value_lines(bad)

    def test_build_url_adds_scheme_and_rejects_empty(self):
        self.assertEqual(build_url('localhost:8080/x', {}), 'http://localhost:8080/x')
        with self.assertRaises(RelayError):
            build_url('   ', {})

    def test_pretty_body_leaves_invalid_json_alone(self):
        self.assertEqual(pretty_body('{not json', 'application/json'), '{not json')

    def test_curl_quotes_shell_characters(self):
        cmd = to_curl(RequestSpec(method='POST', url='https://example.com', body="it's"))
        self.assertIn("--data-raw 'it'\"'\"'s'", cmd)
        self.assertNotIn('--data-raw', to_curl(RequestSpec(method='GET', url='https://example.com', body='ignored')))


class LiveRequestTests(unittest.TestCase):
    def setUp(self):
        self.server = MockServer(port=0); self.server.start()
        self.base = f'http://127.0.0.1:{self.server.port}'
    def tearDown(self):
        self.server.stop()

    def test_get_returns_pretty_json_and_metadata(self):
        r = perform_request(RequestSpec(url=self.base + '/'))
        self.assertEqual(r.status, 200); self.assertEqual(json.loads(r.body)['ok'], True)
        self.assertIn('\n', r.body); self.assertGreater(r.size_bytes, 0)

    def test_http_errors_are_results_not_exceptions(self):
        r = perform_request(RequestSpec(url=self.base + '/missing'))
        self.assertEqual(r.status, 404); self.assertIn('route not found', r.body)

    def test_custom_route_status_and_charset(self):
        self.server.set_route('teapot', MockResponse(418, 'café', {'Content-Type': 'text/plain; charset=utf-8'}))
        r = perform_request(RequestSpec(url=self.base + '/teapot?x=1'))
        self.assertEqual((r.status, r.body), (418, 'café'))

    def test_head_has_no_body(self):
        r = perform_request(RequestSpec(method='HEAD', url=self.base + '/'))
        self.assertEqual((r.status, r.body), (200, ''))

    def test_unreachable_host_raises_relay_error(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
        with self.assertRaises(RelayError):
            perform_request(RequestSpec(url=f'http://127.0.0.1:{port}/'), timeout=2)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(); self.store = RelayStore(Path(self._tmp.name))
    def tearDown(self):
        self._tmp.cleanup()

    def test_history_is_newest_first_and_capped(self):
        for i in range(85): self.store.add_history(RequestSpec(url=f'http://h/{i}'), 200, 1.0)
        h = self.store.history()
        self.assertEqual(len(h), 80); self.assertEqual(h[0]['request']['url'], 'http://h/84')

    def test_saving_same_name_replaces_and_delete_removes(self):
        self.store.save_request('A', RequestSpec(url='http://one')); self.store.save_request('A', RequestSpec(url='http://two'))
        self.assertEqual([s['request']['url'] for s in self.store.saved()], ['http://two'])
        self.store.delete_saved('A'); self.assertEqual(self.store.saved(), [])

    def test_blank_name_falls_back_to_method_and_url(self):
        self.store.save_request('  ', RequestSpec(method='GET', url='http://x'))
        self.assertEqual(self.store.saved()[0]['name'], 'GET http://x')

    def test_corrupt_files_read_as_empty(self):
        self.store.history_path.write_text('{broken'); self.store.saved_path.write_text('{"not": "a list"}')
        self.assertEqual((self.store.history(), self.store.saved()), ([], []))


if __name__ == '__main__':
    unittest.main()
