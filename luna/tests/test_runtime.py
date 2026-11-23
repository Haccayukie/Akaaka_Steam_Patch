from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = load("matching_test", ROOT/"runtime/engine.py")
        cls.data = json.loads(gzip.decompress((ROOT/"runtime/data.json.gz").read_bytes()))
        cls.rules = json.loads((ROOT/"runtime/rules.json").read_text(encoding="utf-8"))
        cls.matcher = cls.engine.Matcher(cls.data, cls.rules)

    def setUp(self):
        self.matcher.history = []

    def test_all_record_ids_and_targets(self):
        records = self.data["records"]
        self.assertEqual([row[0] for row in records], list(range(20722)))
        row = records[16806]
        self.assertEqual(row[5], "因为，这一定不是黑狐的本意。")
        self.assertEqual(row[6], "因為，這一定不是黑狐的本意。")

    def test_native_language_selections(self):
        row = self.data["records"][16806]
        for source, column in [("ja", 2), ("zh", 3), ("cht", 4)]:
            for target, output in [("ja", 2), ("zh", 5), ("cht", 6)]:
                self.matcher.history = []
                self.assertEqual(self.matcher.translate(row[column], source, target), row[output])

    def test_ocr_loses_punctuation_only_line(self):
        self.assertEqual(self.matcher.translate("诶,算了。", "zh", "zh"),
                         self.data["records"][1619][5])

    def test_map_and_known_ocr_alias(self):
        self.assertEqual(self.matcher.translate("路地里", "ja", "zh"), "小巷里")
        self.assertEqual(self.matcher.translate("大阪燒", "cht", "cht"), "御好燒")
        result = self.matcher.translate("社務所\n空大御札授与所\n拝殿\n本殿\n庭\n居間\n廊下\n自分の部屋", "ja", "cht")
        self.assertEqual(result.splitlines(), ["社務所", "護符販賣處", "拜殿", "正殿", "庭園", "起居室", "走廊", "自己的房間"])

    def test_two_choices_return_once(self):
        result = self.matcher.translate("そうかもしれない\nそれでも二人が気になる", "ja", "zh")
        self.assertEqual(result, "或许是这样\n就算如此也在意那两人")

    def test_shout_missing_first_line(self):
        self.assertEqual(self.matcher.translate("ヤッ、ヤベ~", "ja", "zh"),
                         "唔啊！！！！！\n惨、惨了～！！！！！！！！")

    def test_short_reaction_returns_one_with_context(self):
        for row in self.data["records"]:
            if self.engine.body(row[2]) == "ウーン":
                self.matcher.history = [row[0]]
                self.assertEqual(self.matcher.translate("ウーン", "ja", "zh"), row[5])
                break
        else:
            self.fail("Missing reaction source")

    def test_explicit_question_and_ellipsis_direction(self):
        rows = self.data["records"]
        for text in ["………祭り………", "祭り？", "………ウン"]:
            result = self.matcher.translate(text, "ja", "zh")
            self.assertTrue(result)
            if text.endswith("？"):
                self.assertIn("？", result)
            if text == "………祭り………":
                self.assertNotIn("？", result)


class UpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        translator = types.ModuleType("translator")
        base = types.ModuleType("translator.basetranslator")
        base.basetrans = object
        with patch.dict(sys.modules, {"translator": translator, "translator.basetranslator": base}):
            cls.bootstrap = load("bootstrap_test", ROOT/"selfbuild.py")

    def files(self, version="test1"):
        blobs = {
            "engine.py": b"class Matcher: pass\n",
            "data.json.gz": gzip.compress(b'{"records": []}'),
            "rules.json": b"{}",
        }
        manifest = {"version": version, "files": {name: {
            "path": "releases/"+version+"/"+name,
            "sha256": hashlib.sha256(content).hexdigest(),
        } for name, content in blobs.items()}}
        urls = {"https://test/manifest.json": json.dumps(manifest).encode()}
        urls.update({"https://test/releases/"+version+"/"+name: content for name, content in blobs.items()})
        return urls

    def test_valid_update_and_cached_version(self):
        urls = self.files()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(self.bootstrap, "download", side_effect=urls.__getitem__):
                self.bootstrap.update(root, "https://test/")
                self.bootstrap.update(root, "https://test/")
            self.assertEqual(json.loads((root/"current.json").read_text())["version"], "test1")

    def test_failed_checksum_retains_previous_pointer(self):
        urls = self.files("bad")
        urls["https://test/releases/bad/engine.py"] = b"tampered"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.bootstrap.atomic_json(root/"current.json", {"version": "working"})
            with patch.object(self.bootstrap, "download", side_effect=urls.__getitem__):
                with self.assertRaises(ValueError):
                    self.bootstrap.update(root, "https://test/")
            self.assertEqual(json.loads((root/"current.json").read_text())["version"], "working")

    def test_offline_does_not_remove_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.bootstrap.atomic_json(root/"current.json", {"version": "working"})
            with patch.object(self.bootstrap, "download", side_effect=OSError("offline")):
                with self.assertRaises(OSError):
                    self.bootstrap.update(root, "https://test/")
            self.assertEqual(json.loads((root/"current.json").read_text())["version"], "working")

    def test_supported_luna_entry_uses_cached_real_dictionary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = root/"versions/test"
            version.mkdir(parents=True)
            for name in ["engine.py", "data.json.gz", "rules.json"]:
                (version/name).write_bytes((ROOT/"runtime"/name).read_bytes())
            self.bootstrap.atomic_json(root/"current.json", {"version": "test"})
            with patch.object(self.bootstrap, "ROOT", root), patch.object(self.bootstrap, "update", side_effect=OSError("offline")):
                instance = self.bootstrap.TS()
                instance.init()
                instance.srclang_1 = types.SimpleNamespace(code="auto")
                instance.tgtlang_1 = types.SimpleNamespace(code="cht")
                self.assertEqual(instance.translate("路地里"), "小巷裡")
                instance._update_thread.join(5)
                self.assertFalse(instance._update_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
