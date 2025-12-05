#!/usr/bin/env python3
"""Download Java Language Specification - All Chapters"""

import re
from urllib.request import urlopen
from pathlib import Path

def download(url):
    """Download a URL and return content"""
    print(f"  Downloading: {url}")
    with urlopen(url) as response:
        return response.read().decode('latin-1')

def extract_chapter_content(html):
    """Extract clean chapter content, removing navigation and TOC"""
    # Find the main chapter div
    chapter_match = re.search(r'<div lang="en" class="chapter">(.*?)</div>\s*<div class="navfooter">', html, re.DOTALL)
    if not chapter_match:
        return None

    chapter_content = chapter_match.group(1)

    # Remove the TOC div
    chapter_content = re.sub(r'<div class="toc">.*?</div>', '', chapter_content, flags=re.DOTALL)

    return chapter_content

def main():
    base_url = "https://docs.oracle.com/javase/specs/jls/se25/html/"

    # List of chapters to download (19 chapters)
    chapters = [
        ('jls-1.html', 'Chapter 1'),
        ('jls-2.html', 'Chapter 2'),
        ('jls-3.html', 'Chapter 3'),
        ('jls-4.html', 'Chapter 4'),
        ('jls-5.html', 'Chapter 5'),
        ('jls-6.html', 'Chapter 6'),
        ('jls-7.html', 'Chapter 7'),
        ('jls-8.html', 'Chapter 8'),
        ('jls-9.html', 'Chapter 9'),
        ('jls-10.html', 'Chapter 10'),
        ('jls-11.html', 'Chapter 11'),
        ('jls-12.html', 'Chapter 12'),
        ('jls-13.html', 'Chapter 13'),
        ('jls-14.html', 'Chapter 14'),
        ('jls-15.html', 'Chapter 15'),
        ('jls-16.html', 'Chapter 16'),
        ('jls-17.html', 'Chapter 17'),
        ('jls-18.html', 'Chapter 18'),
        ('jls-19.html', 'Chapter 19'),
    ]

    print("Downloading Java SE 25 Language Specification - All Chapters...")
    print(f"Total chapters: {len(chapters)}\n")

    all_content = []

    for filename, title in chapters:
        url = base_url + filename
        print(f"[{title}]")

        html = download(url)
        content = extract_chapter_content(html)

        if content:
            all_content.append(content)
            print(f"  ✓ Extracted\n")
        else:
            print(f"  ✗ Failed to extract\n")

    # Create clean HTML with all chapters
    output = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Java Language Specification - Java SE 25</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 800px; margin: 2em auto; line-height: 1.6; }}
        h1 {{ color: #333; page-break-before: always; margin-top: 2em; }}
        h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 5px; }}
        .chapter {{ margin-bottom: 3em; }}
    </style>
</head>
<body>
<h1>Java Language Specification</h1>
<h2>Java SE 25 Edition</h2>

"""

    for content in all_content:
        output += f'<div class="chapter">\n{content}\n</div>\n<hr>\n'

    output += "</body>\n</html>"

    # Save to file
    output_file = Path("/tmp/jls-se25.html")
    output_file.write_text(output, encoding='utf-8')

    print(f"✅ Saved to: {output_file}")
    print(f"   File size: {len(output) / 1024:.1f} KB")
    print(f"   Chapters: {len(all_content)}")

if __name__ == '__main__':
    main()
