#!/bin/bash
# Build Java Virtual Machine Specification ebook (MOBI + EPUB)
# Single Docker command - downloads, converts, no host dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR}"
TITLE="Java SE 25 VM Specification"
AUTHOR="Oracle"

echo "📚 Building Java VM Specification ebook..."
echo "   Output directory: $OUTPUT_DIR"
echo ""

docker run --rm \
    -v "$SCRIPT_DIR/download_javaspec.py:/app/download.py:ro" \
    -v "$OUTPUT_DIR:/output" \
    ubuntu:22.04 bash -c "
set -e

echo '📦 Installing packages...'
apt-get update -qq
apt-get install -y -qq wget xdg-utils xz-utils python3 libegl1 libopengl0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0 > /dev/null

echo '📥 Installing Calibre...'
wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin > /dev/null 2>&1

echo '📚 Downloading and processing HTML...'
cd /tmp
python3 /app/download.py

echo ''
echo '📱 Converting to MOBI...'
ebook-convert /tmp/jvms-se25.html /output/jvms-se25.mobi \
    --title '$TITLE' \
    --authors '$AUTHOR' \
    --chapter '//h:h1[@class=\"title\"]' \
    --level1-toc '//h:h1[@class=\"title\"]' \
    --level2-toc '//h:h2[@class=\"title\"]' \
    --level3-toc '//h:h3' \
    --use-auto-toc

echo ''
echo '📚 Converting to EPUB...'
ebook-convert /tmp/jvms-se25.html /output/jvms-se25.epub \
    --title '$TITLE' \
    --authors '$AUTHOR' \
    --chapter '//h:h1[@class=\"title\"]' \
    --level1-toc '//h:h1[@class=\"title\"]' \
    --level2-toc '//h:h2[@class=\"title\"]' \
    --level3-toc '//h:h3' \
    --use-auto-toc

echo '✅ Done!'
"

echo ""
echo "✅ Complete! Generated:"
ls -lh "$OUTPUT_DIR"/jvms-se25.*
