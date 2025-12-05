#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat <<-'EOF' | docker build -t chm-to-ebook -f - .
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y wget xz-utils python3 python3-pip unzip \
    libegl1 libopengl0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0
RUN wget -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin
RUN pip3 install beautifulsoup4 lxml
EOF

docker run --rm \
    -v "$SCRIPT_DIR/inside-the-java-virtual-machine.chm:/input/input.chm:ro" \
    -v "$SCRIPT_DIR/clean_html.py:/app/clean_html.py:ro" \
    -v "$SCRIPT_DIR:/output" \
    chm-to-ebook bash -c '
cd /tmp
ebook-convert /input/input.chm extracted --output-profile tablet

python3 /app/clean_html.py extracted/ extracted/inside-the-jvm.html

cd extracted
ebook-convert inside-the-jvm.html /output/inside-the-jvm.mobi \
    --title "Inside the Java Virtual Machine" --authors "Bill Venners" \
    --publisher "McGraw-Hill" --book-producer "McGraw-Hill" \
    --chapter "//h:h2" --level1-toc "//h:h2" --level2-toc "//h:h3" \
    --use-auto-toc --language en

ebook-convert inside-the-jvm.html /output/inside-the-jvm.epub \
    --title "Inside the Java Virtual Machine" --authors "Bill Venners" \
    --publisher "McGraw-Hill" --book-producer "McGraw-Hill" \
    --chapter "//h:h2" --level1-toc "//h:h2" --level2-toc "//h:h3" \
    --use-auto-toc --language en
'

ls -lh "${2:-$SCRIPT_DIR}"/inside-the-jvm.{mobi,epub}
