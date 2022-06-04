import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path


BASE_URL = "https://www.thestudentfoodproject.com/"


def get_recipe_urls():

    recipe_urls = []

    for i in ["/main-courses", "/lunch", "/breakfasts", "/desserts", "/drinks",
              "/vegan"]:
        page = requests.get(BASE_URL + i)
        soup = BeautifulSoup(page.content, 'html.parser')
        for link in soup.find_all(
                "a",
                href=lambda href: href and "/recipes/" in href
        ):
            if link not in recipe_urls:
                recipe_urls.append(link.get("href"))
    print(recipe_urls)
    return recipe_urls


if __name__ == '__main__':
    """Scrapes recipes from The Student Food Project."""
    output_file = Path('../data/studentfoodrecipe.pkl')
    recipe_urls = get_recipe_urls()

    headerList = ['name', 'description', 'nutrition_name', 'nutrition_value',
                  'ingredients', 'method', 'recipe_url']

    data = {"name": [],
            "description": [],
            "nutrition_name": [],
            "nutrition_value": [],
            "ingredients": [],
            "method": [],
            "recipe_url": []}

    prog_bar = tqdm(total=len(recipe_urls))
    prog_bar.set_description(f"Starting download")

    for recipe in recipe_urls:
        recipe_url = BASE_URL + recipe
        recipe_page = requests.get(recipe_url)

        # Get ingredients
        recipe_ingredients = []
        soup = BeautifulSoup(recipe_page.content, 'html.parser')
        recipe_ingredients_p = soup.find(
            'div', class_='recipe-ingrediens w-richtext'
        ).find_all('p')
        for i in recipe_ingredients_p:
            recipe_ingredients.append(i.text)

        # Get method
        recipe_method_p = soup.find(
            'div', class_='recipe-method w-richtext'
        ).find_all('p')
        recipe_method = []
        for i in range(len(recipe_method_p)):
            recipe_method.append(f"Step{i}:{recipe_method_p[i].text}")

        # Get title
        recipe_title = soup.find('h1', class_='recipe-title').text
        prog_bar.set_description(f"Downloading {recipe_title}")

        # Get description
        recipe_desc = soup.find('div', class_='recipe-description').text

        # Add everything to data
        data["name"].append(recipe_title)
        data["description"].append(recipe_desc)
        data["nutrition_name"].append(None)
        data["nutrition_value"].append(None)
        data["ingredients"].append(recipe_ingredients)
        data["method"].append(recipe_method)
        data["recipe_url"].append(recipe_url)

        prog_bar.update(1)

    data_df = pd.DataFrame(data)
    data_df.to_pickle(str(output_file))
