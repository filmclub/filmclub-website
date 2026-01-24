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


def front_matter_bounds(lines):
    if not lines or not lines[0].strip().startswith('---'):
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


def get_letterboxd_id(lines, start, end):
    for ln in lines[start+1:end]:
        if ln.strip().startswith('letterboxd_id:'):
            val = ln.split(':', 1)[1].strip()
            return val if val else None
    return None


def main():
    # Collect all film titles that have letterboxd_id
    films_with_ids = set()

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
                continue
            start, end = bounds
            title = extract_title(lines, start, end)
            lb_id = get_letterboxd_id(lines, start, end)
            
            if title and lb_id:
                films_with_ids.add(normalize(title))

    print(f"Found {len(films_with_ids)} films with letterboxd_id in markdown")

    # Read CSV and keep only header + rows without letterboxd_id
    rows_to_keep = []
    removed_count = 0

    with CSV_PATH.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['Name'].strip()
            if normalize(title) not in films_with_ids:
                rows_to_keep.append(row)
            else:
                removed_count += 1

    # Write back
    if rows_to_keep:
        with CSV_PATH.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Date', 'Name', 'Year', 'Letterboxd URI'])
            writer.writeheader()
            writer.writerows(rows_to_keep)
    else:
        # Just header
        with CSV_PATH.open('w') as f:
            f.write("Date,Name,Year,Letterboxd URI\n")

    print(f"Removed {removed_count} films from CSV")
    print(f"Kept {len(rows_to_keep)} films")


if __name__ == '__main__':
    main()
