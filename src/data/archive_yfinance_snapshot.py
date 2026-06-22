#!/usr/bin/env python3
"""Create an immutable gzip-compressed content-addressed archive of a snapshot."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive(snapshot: Path, store: Path, manifest_path: Path) -> dict:
    objects = store / "objects"
    objects.mkdir(parents=True, exist_ok=True)
    files, logical_bytes, new_compressed_bytes = [], 0, 0
    for path in sorted(p for p in snapshot.rglob("*") if p.is_file()):
        raw = path.read_bytes()
        checksum = digest(raw)
        target = objects / checksum[:2] / f"{checksum}.gz"
        created = not target.exists()
        if created:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
            new_compressed_bytes += target.stat().st_size
        logical_bytes += len(raw)
        files.append({"path": str(path.relative_to(snapshot)), "sha256": checksum, "bytes": len(raw),
                      "object": str(target.relative_to(store)), "compressed_bytes": target.stat().st_size, "object_created": created})
    payload = {"schema": "YF-CAS-1.0.0", "snapshot": str(snapshot), "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "file_count": len(files), "logical_bytes": logical_bytes,
               "referenced_compressed_bytes": sum(x["compressed_bytes"] for x in files),
               "new_compressed_bytes": new_compressed_bytes, "files": files}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(archive(args.snapshot, args.store, args.manifest)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
