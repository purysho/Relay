import json
import tempfile
import unittest
from pathlib import Path

from relay.http_client import build_url, parse_key_value_lines, pretty_body, to_curl
from relay.models import RequestSpec
from relay.storage import RelayStore

class RelayCoreTests(unittest.TestCase):
    def test_parse_pairs(self): self.assertEqual(parse_key_value_lines("Accept: application/json\npage=2"), {"Accept":"application/json","page":"2"})
    def test_build_url_preserves_existing_query(self):
        url=build_url("https://example.com/api?x=1",{"page":"2"}); self.assertIn("x=1",url); self.assertIn("page=2",url)
    def test_pretty_json(self):
        result=pretty_body('{"ok":true}',"application/json"); self.assertEqual(json.loads(result),{"ok":True}); self.assertIn("\n",result)
    def test_curl(self):
        cmd=to_curl(RequestSpec(method="POST",url="https://example.com",headers={"X-Test":"yes"},body="hello")); self.assertIn("curl -X POST",cmd); self.assertIn("X-Test: yes",cmd)
    def test_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=RelayStore(Path(tmp)); spec=RequestSpec(url="https://example.com"); store.save_request("Example",spec); self.assertEqual(store.saved()[0]["name"],"Example"); store.add_history(spec,200,12.4); self.assertEqual(store.history()[0]["status"],200)
if __name__=="__main__": unittest.main()
