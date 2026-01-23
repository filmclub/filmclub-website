import csv
import re
from pathlib import Path

CSV_PATH = Path('/home/bartd/Downloads/letterboxd-bdu-2026-01-23-16-52-utc/watched.csv')
ARCHIEF_DIR = Path('/home/bartd/Source/filmclub-website/content/archief')


def normalize(title: str) -> str:
    t = title.lower()
    t = t.replace(' & ', '-and-').replace('&', 'and')
    t = re.sub(r"[^\w\s-]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"-+", "-", t)
    return t.strip('-')


def load_letterboxd_map(csv_path: Path):
    mapping = {}
    with csv_path.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Name'].strip()
            url = row['Letterboxd URI']
            lb_id = url.split('/')[-1]
            mapping[normalize(name)] = lb_id
    return mapping


def extract_title_from_front_matter(lines):
    # front matter between first and second '---'
    if not lines or not lines[0].strip().startswith('---'):
        return None
    for i in range(1, len(lines)):
        if lines[i].strip().startswith('---'):
            end = i
            break
    else:
        return None
    fm_lines = lines[1:end]
    for ln in fm_lines:
        if ln.lower().startswith('title:'):
            # title: "..." or plain
            val = ln.split(':', 1)[1].strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            return val
    return None


def front_matter_bounds(lines):
    if not lines or not lines[0].strip().startswith('---'):
        return None
    for i in range(1, len(lines)):
        if lines[i].strip().startswith('---'):
            return (0, i)
    return None


def has_letterboxd_id(lines, start, end):
    for ln in lines[start+1:end]:
        if ln.strip().startswith('letterboxd_id:'):
            return True
    return False


def insert_letterboxd_id(lines, start, end, lb_id):
    insert_idx = end  # before closing '---'
    new_line = f"letterboxd_id: {lb_id}\n"
    return lines[:insert_idx] + [new_line] + lines[insert_idx:]


def main():
    lb_map = load_letterboxd_map(CSV_PATH)
    md_files = sorted([p for p in ARCHIEF_DIR.glob('*.md') if p.name != '_index.md'])

    added = 0
    matched = 0
    unmatched = []

    for p in md_files:
        text = p.read_text()
        lines = text.splitlines(keepends=True)
        bounds = front_matter_bounds(lines)
        if not bounds:
            unmatched.append(p.name)
            continue
        start, end = bounds
        if has_letterboxd_id(lines, start, end):
            continue
        # try filename and title
        fn_key = p.stem
        title = extract_title_from_front_matter(lines)
        title_key = normalize(title) if title else None

        lb_id = None
        if fn_key in lb_map:
            lb_id = lb_map[fn_key]
        elif title_key and title_key in lb_map:
            lb_id = lb_map[title_key]

        if lb_id:
            matched += 1
            new_lines = insert_letterboxd_id(lines, start, end, lb_id)
            p.write_text(''.join(new_lines))
            added += 1
        else:
            unmatched.append(p.name)

    print(f"Added letterboxd_id to {added} files")
    if unmatched:
        print(f"Unmatched {len(unmatched)} files (no CSV match):")
        for name in unmatched[:30]:
            print(f"  - {name}")


if __name__ == '__main__':
    main()
