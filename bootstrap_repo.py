from __future__ import annotations

import base64
import io
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent
payload = "".join(
    (root / ".bootstrap" / f"chunk{i:02d}").read_text().strip()
    for i in range(5)
)
raw = base64.b64decode(payload)

with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
    root_resolved = root.resolve()
    for member in archive.getmembers():
        target = (root / member.name).resolve()
        if root_resolved not in target.parents and target != root_resolved:
            raise RuntimeError(f"Unsafe path in archive: {member.name}")
    archive.extractall(root)

print("Expanded production ML repository.")
