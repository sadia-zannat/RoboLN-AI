"""Verify every file listed in the release SHA-256 manifest from an extracted ZIP."""
from pathlib import Path
import hashlib,sys
root=Path(__file__).resolve().parents[1]
manifest=root/'RELEASE_SHA256SUMS.txt'
checks=0
for line in manifest.read_text(encoding='utf-8').splitlines():
    if not line or line.startswith('#'):continue
    expected,relative=line.split('  ',1)
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():raise SystemExit('Missing/unsafe manifest file: '+relative)
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=expected:raise SystemExit('Hash mismatch: '+relative)
    checks+=1
print(f'SHA-256 manifest: {checks} files verified')
