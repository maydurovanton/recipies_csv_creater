# Recipe Scraper

This project provides scripts to scrape recipes from a web site into a CSV file
and download recipe photos.

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the `DEEPL_API_KEY` environment variable if you want automatic translation
using the DeepL API.

## Usage

### Scrape Recipes

```bash
python scrape_recipes.py <START_URL> [OUTPUT_DIR]
```

The script will crawl the given `START_URL`, collect recipe information and
store it in `OUTPUT_DIR` (default `output`). For each recipe it creates text
files containing photo URLs, ingredients and steps. The main data is saved to
`recipes.csv`.

### Download Images

```bash
python download_images.py <TXT_DIR> [IMAGES_DIR]
```

Reads `*_photos.txt` files from `TXT_DIR` and downloads all images into
`IMAGES_DIR` (default `images`).
