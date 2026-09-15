#!/usr/bin/env python3
"""Check public candidate files, local links and the measurement contract."""
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate():
    errors = []
    files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    forbidden = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AIza[A-Za-z0-9_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|/Users/[A-Za-z0-9._-]+/|wordpress_logged_in_[a-f0-9]+)')
    for name in sorted(set(files) - {''}):
        path = ROOT / name
        if not path.is_file():
            errors.append(f'Missing tracked file: {name}')
            continue
        if path.suffix not in {'.md', '.json', '.js', '.py', '.svg', '.yml', '.yaml', ''}:
            errors.append(f'Unreviewed public file type: {name}')
            continue
        content = path.read_text(encoding='utf-8')
        if forbidden.search(content):
            errors.append(f'Sensitive pattern in {name}')
        if path.suffix == '.md':
            content = re.sub(r'```.*?```', '', content, flags=re.S)
            for link in re.findall(r'\]\(([^)]+)\)', content):
                if re.match(r'^(?:https?://|mailto:|#)', link):
                    continue
                target = (path.parent / link.split('#')[0]).resolve()
                if not target.is_relative_to(ROOT) or not target.exists():
                    errors.append(f'Broken/outside link in {name}: {link}')
    spec = importlib.util.spec_from_file_location('comparison', ROOT / 'scripts/compare-search-windows.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = json.loads((ROOT / 'data/search-checkpoint-2026-09-14.json').read_text())
    mod.compare(data)
    for side in ('before', 'after'):
        for metric in ('clicks', 'impressions'):
            if sum(p[side][metric] for p in data['pages']) != data['cohorts']['english_mvp'][side][metric]:
                errors.append(f'MVP page sum disagrees: {side}/{metric}')
    recrawl = json.loads((ROOT / 'data/recrawl-checkpoint-2026-09-16.json').read_text())
    if sum(p['advanced'] for p in recrawl['pages']) != 2:
        errors.append('Recrawl summary disagrees with published 2/3 result')
    print(json.dumps({'pass': not errors, 'files_checked': len(set(files)-{''}), 'errors': errors}, ensure_ascii=False, indent=2))
    return not errors


if __name__ == '__main__':
    raise SystemExit(0 if validate() else 1)
