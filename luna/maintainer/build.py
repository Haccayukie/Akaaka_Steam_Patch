"""Build an immutable update snapshot after editing runtime text/rules/code."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil


ROOT = Path(__file__).resolve().parents[1]


def build():
    runtime = ROOT / "runtime"
    data = json.loads(gzip.decompress((runtime / "data.json.gz").read_bytes()))
    assert len(data["records"]) == 20722
    assert len({record[0] for record in data["records"]}) == 20722
    assert all(len(record) == 7 for record in data["records"])
    compile((runtime / "engine.py").read_text(encoding="utf-8"), "engine.py", "exec")
    rules = json.loads((runtime / "rules.json").read_text(encoding="utf-8"))
    assert 0 < rules["similarity"] <= 1
    names = ["engine.py", "data.json.gz", "rules.json"]
    hashes = {name: hashlib.sha256((runtime/name).read_bytes()).hexdigest() for name in names}
    version = "v1-" + hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    release = ROOT / "releases" / version
    release.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in names:
        shutil.copyfile(runtime/name, release/name)
        files[name] = {"path": "releases/"+version+"/"+name, "sha256": hashes[name]}
    manifest = {"schema": 1, "version": version, "records": len(data["records"]),
                "bootstrap_sha256": hashlib.sha256((ROOT/"selfbuild.py").read_bytes()).hexdigest(),
                "files": files}
    (ROOT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(version)
    return manifest


if __name__ == "__main__":
    build()
