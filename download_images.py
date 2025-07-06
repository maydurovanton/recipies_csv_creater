import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests


def download_image(url: str, dest_folder: Path) -> None:
    dest_folder.mkdir(parents=True, exist_ok=True)
    name = os.path.basename(urlparse(url).path)
    if not name:
        name = "image"
    path = dest_folder / name
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to download {url}: {exc}")
        return
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"Saved {url} -> {path}")


def download_from_txt(txt_path: Path, dest_folder: Path) -> None:
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url:
                download_image(url, dest_folder)


def main(txt_dir: str, dest_folder: str = "images"):
    txt_dir = Path(txt_dir)
    dest = Path(dest_folder)
    for txt_file in txt_dir.glob("*_photos.txt"):
        download_from_txt(txt_file, dest)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_images.py TXT_DIR [IMAGES_DIR]")
        sys.exit(1)
    txt_dir = sys.argv[1]
    images_dir = sys.argv[2] if len(sys.argv) > 2 else "images"
    main(txt_dir, images_dir)
