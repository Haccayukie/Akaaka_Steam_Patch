"""Edit an existing release translation by stable text ID."""
from pathlib import Path
import argparse
import gzip
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("id", type=int)
    parser.add_argument("--zh")
    parser.add_argument("--cht")
    args = parser.parse_args()
    if args.zh is None and args.cht is None:
        parser.error("请至少提供 --zh 或 --cht")
    path = Path(__file__).resolve().parents[1]/"runtime/data.json.gz"
    data = json.loads(gzip.decompress(path.read_bytes()))
    record = next(row for row in data["records"] if row[0] == args.id)
    if args.zh is not None:
        record[5] = args.zh.replace("<br>", "\n")
    if args.cht is not None:
        record[6] = args.cht.replace("<br>", "\n")
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
    path.write_bytes(gzip.compress(encoded, mtime=0))


if __name__ == "__main__":
    main()
