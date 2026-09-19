#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
src=(root/'src/main.scmd').read_text(encoding='utf-8')
# Scan the whole compiled package (pages/, lazy/, bootstrap.cfg, entry.cfg, ...):
# since 0.11+ the boot-path registration lives in bootstrap.cfg, not pages/.
pkg=root/'build/Scmd'
pages='\n'.join(p.read_text(encoding='utf-8') for p in sorted(pkg.rglob('*.cfg')))
funcs=[]
for line in src.splitlines():
    m=re.match(r'// fn\[(\d+)\] ([A-Za-z0-9_]+)(?: -> ([A-Za-z0-9_]+))?', line)
    if m: funcs.append((int(m.group(1)),m.group(2),m.group(3)))
errors=[]
for idx,name,alias in funcs:
    if f'alias __scmd_fn{idx} ' not in pages:
        errors.append(f'missing function alias __scmd_fn{idx} ({name})')
    if alias and f'alias {alias} __scmd_fn{idx}' not in pages:
        # registration exists inside a generated function body, so search textual body fragment too
        if f'alias {alias} __scmd_fn{idx};' not in pages and f'alias {alias} __scmd_fn{idx}' not in pages:
            errors.append(f'missing registration literal for {alias} -> __scmd_fn{idx}')
if errors:
    print('VERIFY_FAIL')
    print('\n'.join(errors[:50]))
    sys.exit(1)
print(f'VERIFY_PASS functions={len(funcs)} public_entries={sum(1 for _,_,a in funcs if a)}')
