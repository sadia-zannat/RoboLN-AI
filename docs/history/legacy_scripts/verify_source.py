"""Check file-level hashes generated in RELEASE_SHA256SUMS.txt (exclude itself)."""
import hashlib,sys,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
manifest=root/'RELEASE_SHA256SUMS.txt'
if not manifest.exists():raise SystemExit('Manifest missing')
lines=manifest.read_text().splitlines()
for row in lines:
    expect,rel=row.split('  ',1)
    p=(root/rel).resolve()
    if not p.is_relative_to(root) or not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=expect:
        raise SystemExit(f'HASH MISMATCH {rel}')
print(f'Verified {len(lines)} source file hashes')
