#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

docker run --rm \
    -v "$SCRIPT_DIR/download_javaspec.py:/app/download.py:ro" \
    -v "$SCRIPT_DIR:/output" \
    ubuntu:22.04 bash -c '

apt-get update
apt-get install -y wget xdg-utils xz-utils python3 libegl1 libopengl0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0

wget -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

cd /tmp
python3 /app/download.py

ebook-convert /tmp/jvms-se25.html /output/jvms-se25.mobi \
    --title "Java SE 25 VM Specification" \
    --authors "Oracle" \
    --chapter "//h:h1[@class=\"title\"]" \
    --level1-toc "//h:h1[@class=\"title\"]" \
    --level2-toc "//h:h2[@class=\"title\"]" \
    --level3-toc "//h:h3" \
    --use-auto-toc

ebook-convert /tmp/jvms-se25.html /output/jvms-se25.epub \
    --title "Java SE 25 VM Specification" \
    --authors "Oracle" \
    --chapter "//h:h1[@class=\"title\"]" \
    --level1-toc "//h:h1[@class=\"title\"]" \
    --level2-toc "//h:h2[@class=\"title\"]" \
    --level3-toc "//h:h3" \
    --use-auto-toc
'
