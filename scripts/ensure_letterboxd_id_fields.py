import csv
import re
from pathlib import Path

CSV_PATH = Path('/home/bartd/Downloads/letterboxd-bdu-2026-01-23-16-52-utc/watched.csv')
CONTENT_DIRS = [
    Path('/home/bartd/Source/filmclub-website/content/archief'),
    Path('/home/bartd/Source/filmclub-website/content/gepland'),
]


def normalize(title: str) -> str:
    t = title.lower()
    t = t.replace(' & ', '-and-').replace('&', 'and')
    t = re.sub(r"[^\w\s-]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"-+", "-", t)
    return t.strip('-')


def load_letterboxd_map(csv_path: Path):
    mapping = {}
    if not csv_path.exists():
        return mapping
    with csv_path.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Name'].strip()
            url = row['Letterboxd URI']
            lb_id = url.split('/')[-1]
            mapping[normalize(name)] = lb_id
    return mapping


def front_matter_bounds(lines):
    if not lines:
        return None
    if not lines[0].strip().startswith('---'):
        return None
    for i in range(1, len(lines)):
        if lines[i].strip().startswith('---'):
            return 0, i
    return None


def extract_title(lines, start, end):
    for ln in lines[start+1:end]:
        if ln.lower().startswith('title:'):
            val = ln.split(':', 1)[1].strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            return val
    return None


def has_letterboxd_id(lines, start, end):
    for idx in range(start+1, end):
        if lines[idx].strip().startswith('letterboxd_id:'):
            return True
    return False


def insert_letterboxd_id(lines, start, end, value: str | None):
    insert_idx = end
    lb_line = f"letterboxd_id: {value if value else ''}\n"
    return lines[:insert_idx] + [lb_line] + lines[insert_idx:]


def main():
    lb_map = load_letterboxd_map(CSV_PATH)

    counts = {
        'updated_with_id': 0,
        'added_blank': 0,
        'already_present': 0,
        'skipped_no_fm': 0,
        'processed': 0,
    }

    for folder in CONTENT_DIRS:
        if not folder.exists():
            continue
        for p in sorted(folder.glob('*.md')):
            if p.name == '_index.md':
                continue
            text = p.read_text()
            lines = text.splitlines(keepends=True)
            bounds = front_matter_bounds(lines)
            if not bounds:
                counts['skipped_no_fm'] += 1
                continue
            start, end = bounds
            if has_letterboxd_id(lines, start, end):
                counts['already_present'] += 1
                continue

            # Try to find an ID from CSV
            fn_key = p.stem
            title = extract_title(lines, start, end)
            title_key = normalize(title) if title else None

            lb_id = None
            if fn_key in lb_map:
                lb_id = lb_map[fn_key]
            elif title_key and title_key in lb_map:
                lb_id = lb_map[title_key]

            new_lines = insert_letterboxd_id(lines, start, end, lb_id)
            p.write_text(''.join(new_lines))
            if lb_id:
                counts['updated_with_id'] += 1
            else:
                counts['added_blank'] += 1
            counts['processed'] += 1

    print("Done.")
    for k, v in counts.items():
        print(f"{k}: {v}")


if __name__ == '__main__':
    main()
