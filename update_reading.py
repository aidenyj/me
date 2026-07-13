#!/usr/bin/env python3
"""Regenerate reading.html from Chrome bookmarks (Reading folder)."""

import json, os
from collections import defaultdict
from datetime import datetime, timedelta

BOOKMARKS_PATH = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Bookmarks"
)
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "reading.html")


def chrome_time_to_datetime(ts):
    return datetime(1601, 1, 1) + timedelta(microseconds=int(ts))


def find_folder(node, target_name):
    if node.get("type") == "folder" and node.get("name") == target_name:
        return node
    for child in node.get("children", []):
        result = find_folder(child, target_name)
        if result:
            return result
    return None


def extract_bookmarks(node, results=None):
    if results is None:
        results = []
    if node.get("type") == "url":
        dt = chrome_time_to_datetime(node.get("date_added", "0"))
        results.append({
            "title": node.get("name", ""),
            "url": node.get("url", ""),
            "date_added": dt,
        })
    for child in node.get("children", []):
        extract_bookmarks(child, results)
    return results


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_html(bookmarks):
    bookmarks.sort(key=lambda x: x["date_added"], reverse=True)

    months = defaultdict(list)
    for b in bookmarks:
        key = b["date_added"].strftime("%B %Y")
        months[key].append(b)

    month_order = list(dict.fromkeys(
        b["date_added"].strftime("%B %Y") for b in bookmarks
    ))

    sections = ""
    for i, month in enumerate(month_order):
        articles = months[month]
        open_attr = " open" if i == 0 else ""
        sections += f'      <details{open_attr}>\n'
        sections += f'        <summary>{month} <span class="count">({len(articles)})</span></summary>\n'
        sections += f'        <ul class="reading-list">\n'
        for a in articles:
            date_str = a["date_added"].strftime("%b %-d")
            sections += f'          <li><span class="date">{date_str}</span><a href="{esc(a["url"])}">{esc(a["title"])}</a></li>\n'
        sections += f'        </ul>\n'
        sections += f'      </details>\n'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reading — Aiden Jeong</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <a href="index.html" class="back" aria-label="Home"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></a>
    <h1>reading</h1>
    <p class="reading-intro">{len(bookmarks)} articles I've bookmarked.</p>
    <input type="text" class="reading-search" placeholder="Search articles..." autofocus>
{sections}  </div>
  <script>
    document.querySelector('.reading-search').addEventListener('input', function () {{
      const q = this.value.toLowerCase();
      document.querySelectorAll('details').forEach(function (section) {{
        let visible = 0;
        section.querySelectorAll('li').forEach(function (li) {{
          const match = !q || li.textContent.toLowerCase().includes(q);
          li.classList.toggle('hidden', !match);
          if (match) visible++;
        }});
        section.classList.toggle('hidden', visible === 0);
        if (q && visible > 0) section.open = true;
      }});
    }});
  </script>
</body>
</html>'''


def main():
    with open(BOOKMARKS_PATH) as f:
        data = json.load(f)

    reading_folder = None
    for root in data["roots"].values():
        if isinstance(root, dict):
            reading_folder = find_folder(root, "Reading")
            if reading_folder:
                break

    if not reading_folder:
        print("Error: 'Reading' folder not found in bookmarks.")
        return

    bookmarks = extract_bookmarks(reading_folder)
    html = build_html(bookmarks)

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"Updated {OUTPUT_PATH} — {len(bookmarks)} articles")


if __name__ == "__main__":
    main()
