import csv
import os
import re
import sys
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# Configure a requests session with a browser-like User-Agent and retries
session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
)
retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504, 403])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)
from bs4 import BeautifulSoup

try:
    import deepl
except ImportError:
    deepl = None


def slugify(value: str) -> str:
    """Simple slugify function for filenames."""
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[\s-]+", "-", value)


def translate(text: str, translator) -> str:
    if not text:
        return text
    if translator is None:
        return text
    result = translator.translate_text(text, target_lang="RU")
    return result.text


def extract_recipe_links(start_url: str) -> list[str]:
    """Example function to extract recipe links from start_url."""
    response = session.get(start_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if "recipe" in href:
            links.append(urljoin(start_url, href))
    return list(dict.fromkeys(links))  # remove duplicates


def parse_recipe(url: str) -> dict:
    """Parse a recipe page. This function may need adjustments per site."""
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    name = soup.find("h1").get_text(strip=True)
    recipe_type = soup.find("div", class_="type")
    recipe_type = recipe_type.get_text(strip=True) if recipe_type else ""

    ingredients = []
    for li in soup.select("li.ingredient"):
        ingredients.append(li.get_text(strip=True))

    prep_time = soup.select_one("time.prep")
    cook_time = soup.select_one("time.cook")
    total_time = soup.select_one("time.total")
    prep_time = prep_time.get_text(strip=True) if prep_time else ""
    cook_time = cook_time.get_text(strip=True) if cook_time else ""
    total_time = total_time.get_text(strip=True) if total_time else ""

    steps = [p.get_text(strip=True) for p in soup.select("div.steps p")]

    photo_urls = []
    for img in soup.select("img"):  # adjust selector per site
        src = img.get("src")
        if src and any(src.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
            photo_urls.append(urljoin(url, src))

    return {
        "name": name,
        "type": recipe_type,
        "ingredients": ingredients,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "total_time": total_time,
        "steps": steps,
        "photos": photo_urls,
    }


def normalize_ingredients(ingredients: list[str]) -> list[str]:
    seen = set()
    result = []
    for ing in ingredients:
        norm = ing.lower().strip()
        if norm not in seen:
            seen.add(norm)
            result.append(ing)
    return result


def main(start_url: str, output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    translator = None
    api_key = os.environ.get("DEEPL_API_KEY")
    if api_key and deepl:
        translator = deepl.Translator(api_key)
    links = extract_recipe_links(start_url)
    csv_path = os.path.join(output_dir, "recipes.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Название",
            "Тип",
            "Ингредиенты",
            "Время на подготовку",
            "Время на готовку",
            "Всего времени",
        ])
        for url in links:
            try:
                data = parse_recipe(url)
            except Exception as exc:
                print(f"Failed to parse {url}: {exc}")
                continue
            data["ingredients"] = normalize_ingredients(data["ingredients"])
            if translator:
                data["name"] = translate(data["name"], translator)
                data["type"] = translate(data["type"], translator)
                data["ingredients"] = [translate(i, translator) for i in data["ingredients"]]
                data["prep_time"] = translate(data["prep_time"], translator)
                data["cook_time"] = translate(data["cook_time"], translator)
                data["total_time"] = translate(data["total_time"], translator)
                data["steps"] = [translate(s, translator) for s in data["steps"]]
            slug = slugify(data["name"])
            text_dir = os.path.join(output_dir, "text")
            os.makedirs(text_dir, exist_ok=True)
            with open(os.path.join(text_dir, f"{slug}_photos.txt"), "w", encoding="utf-8") as f:
                for p in data["photos"]:
                    f.write(p + "\n")
            with open(os.path.join(text_dir, f"{slug}_ingredients.txt"), "w", encoding="utf-8") as f:
                for ing in data["ingredients"]:
                    f.write(ing + "\n")
            with open(os.path.join(text_dir, f"{slug}_steps.txt"), "w", encoding="utf-8") as f:
                for step in data["steps"]:
                    f.write(step + "\n")
            writer.writerow([
                data["name"],
                data["type"],
                ", ".join(data["ingredients"]),
                data["prep_time"],
                data["cook_time"],
                data["total_time"],
            ])
    print(f"Saved recipes to {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape_recipes.py START_URL [OUTPUT_DIR]")
        sys.exit(1)
    start_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    main(start_url, output_dir)
