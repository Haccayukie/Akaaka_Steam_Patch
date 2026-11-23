"""Luna's supported custom translator entry point; official files stay intact."""
from translator.basetranslator import basetrans
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import os
import threading
import time
import urllib.request


ROOT = Path(__file__).resolve().parent / "akaaka_pretranslation"
BASE_URL = "https://raw.githubusercontent.com/Haccayukie/Akaaka_Steam_Patch/main/luna/"
MAX_DOWNLOAD = 32 * 1024 * 1024


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Akaaka-Luna-Pretranslation/1"})
    with urllib.request.urlopen(request, timeout=8) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError("更新文件超过大小限制")
    return data


def _update_once(root, base_url):
    root.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(download(base_url + "manifest.json").decode("utf-8-sig"))
    version = manifest["version"]
    if not version or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in version):
        raise ValueError("无效版本号")
    destination = root / "versions" / version
    complete = destination / "complete.json"
    if not complete.exists():
        destination.mkdir(parents=True, exist_ok=True)
        for name in ["engine.py", "data.json.gz", "rules.json"]:
            item = manifest["files"][name]
            relative = item["path"]
            if relative.startswith("/") or ".." in relative.split("/") or ":" in relative:
                raise ValueError("无效更新路径")
            content = download(base_url + relative)
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("更新文件校验失败")
            temporary = destination / (name + ".tmp")
            temporary.write_bytes(content)
            os.replace(temporary, destination / name)
        # A failed update never replaces the working version pointer.
        compile((destination / "engine.py").read_text(encoding="utf-8"), "engine.py", "exec")
        json.loads(gzip.decompress((destination / "data.json.gz").read_bytes()))
        json.loads((destination / "rules.json").read_text(encoding="utf-8"))
        atomic_json(complete, {"version": version})
    atomic_json(root / "current.json", {"version": version})
    atomic_json(root / "status.json", {"version": version, "checked_at": time.time(), "error": ""})


def update(root=ROOT, base_url=BASE_URL):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "update.lock"
    # Two Luna instances must not replace a version while another downloads it.
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if time.time() - lock.stat().st_mtime <= 900:
            return
        lock.unlink(missing_ok=True)
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.close(descriptor)
        _update_once(root, base_url)
    finally:
        lock.unlink(missing_ok=True)


class TS(basetrans):
    def init(self):
        # Luna's wrapper can call init again after constructing this class.
        if getattr(self, "_initialized", False):
            return
        self._lock = threading.RLock()
        self._version = None
        self._matcher = None
        self._load_current()
        self._initialized = True
        self._update_thread = threading.Thread(target=self._update_background, daemon=True)
        self._update_thread.start()

    def _load_current(self):
        with self._lock:
            pointer = ROOT / "current.json"
            if not pointer.exists():
                return
            version = json.loads(pointer.read_text(encoding="utf-8"))["version"]
            if self._version == version:
                return
            directory = ROOT / "versions" / version
            spec = importlib.util.spec_from_file_location("akaaka_matching_engine", directory / "engine.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            data = json.loads(gzip.decompress((directory / "data.json.gz").read_bytes()))
            rules = json.loads((directory / "rules.json").read_text(encoding="utf-8"))
            matcher = module.Matcher(data, rules)
            self._matcher = matcher
            self._version = version

    def _update_background(self):
        try:
            update()
            self._load_current()
        except Exception as error:
            # Local cache remains usable while GitHub is unreachable.
            try:
                atomic_json(ROOT / "status.json", {"checked_at": time.time(), "error": str(error)})
            except OSError:
                pass

    def translate(self, content):
        with self._lock:
            if self._matcher is None:
                raise RuntimeError("本地词库未安装完成，请重新运行安装入口")
            source = self.srclang_1.code
            target = self.tgtlang_1.code
            result = self._matcher.translate(content, source, target)
            return result or ""
