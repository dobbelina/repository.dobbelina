#!/usr/bin/env python
"""
Get logo dimensions using just struct parsing (no PIL required)
"""

import os
import struct

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "plugin.video.cumination", "resources", "images")


def get_png_dimensions(filepath):
    """Get PNG dimensions by reading header"""
    with open(filepath, "rb") as f:
        # PNG signature
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            return None
        # IHDR chunk
        f.read(4)  # chunk length
        if f.read(4) != b"IHDR":
            return None
        width, height = struct.unpack(">II", f.read(8))
        return (width, height)


def get_gif_dimensions(filepath):
    """Get GIF dimensions by reading header"""
    with open(filepath, "rb") as f:
        if f.read(6) not in (b"GIF87a", b"GIF89a"):
            return None
        width, height = struct.unpack("<HH", f.read(4))
        return (width, height)


def get_jpg_dimensions(filepath):
    """Get JPG dimensions by reading JPEG markers"""
    with open(filepath, "rb") as f:
        if f.read(2) != b"\xff\xd8":
            return None
        while True:
            marker = f.read(2)
            if len(marker) != 2:
                return None
            if marker[0] != 0xFF:
                return None
            if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                f.read(3)  # skip length and precision
                height, width = struct.unpack(">HH", f.read(4))
                return (width, height)
            elif marker[1] == 0xD9:  # EOI
                return None
            else:
                length = struct.unpack(">H", f.read(2))[0]
                f.read(length - 2)


def get_image_dimensions(filepath):
    """Get image dimensions based on file type"""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".png":
            return get_png_dimensions(filepath)
        elif ext == ".gif":
            return get_gif_dimensions(filepath)
        elif ext in (".jpg", ".jpeg"):
            return get_jpg_dimensions(filepath)
    except:
        return None
    return None


def main():
    """Analyze all logo dimensions"""
    results = []

    for filename in sorted(os.listdir(IMAGES_DIR)):
        if filename.lower().endswith(
            (".png", ".jpg", ".gif")
        ) and not filename.startswith("cum-"):
            filepath = os.path.join(IMAGES_DIR, filename)
            dims = get_image_dimensions(filepath)
            if dims:
                width, height = dims
                size_kb = os.path.getsize(filepath) / 1024
                results.append((width, height, size_kb, filename))
            else:
                results.append((0, 0, os.path.getsize(filepath) / 1024, filename))

    # Sort by area
    results.sort(key=lambda x: x[0] * x[1])

    print("=" * 90)
    print("LOGO DIMENSIONS REPORT")
    print("=" * 90)
    print(f"{'Width':<7} {'Height':<7} {'Size':<10} {'Filename':<50}")
    print("-" * 90)

    for width, height, size_kb, filename in results:
        if width > 0:
            print(f"{width:<7} {height:<7} {size_kb:>7.1f} KB {filename:<50}")
        else:
            print(f"{'ERROR':<7} {'ERROR':<7} {size_kb:>7.1f} KB {filename:<50}")

    print()
    print("Statistics:")
    widths = [r[0] for r in results if r[0] > 0]
    heights = [r[1] for r in results if r[1] > 0]
    sizes = [r[2] for r in results]

    if widths:
        print(
            f"  Width:  min={min(widths)}px, max={max(widths)}px, avg={sum(widths) // len(widths)}px"
        )
        print(
            f"  Height: min={min(heights)}px, max={max(heights)}px, avg={sum(heights) // len(heights)}px"
        )
        print(
            f"  Size:   min={min(sizes):.1f}KB, max={max(sizes):.1f}KB, avg={sum(sizes) / len(sizes):.1f}KB"
        )


if __name__ == "__main__":
    main()
