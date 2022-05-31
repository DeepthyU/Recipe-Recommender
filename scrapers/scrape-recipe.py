import requests
import csv
from bs4 import BeautifulSoup
from tqdm import tqdm

file = open('../data/studentfoodrecipe.csv', 'a')

base_url = "https://www.thestudentfoodproject.com/"
writer = csv.writer(file, delimiter=";")
recipe_urls = []
for i in ["/main-courses", "/lunch", "/breakfasts", "/desserts", "/drinks", "/vegan"]:
    page = requests.get(base_url + i)
    soup = BeautifulSoup(page.content, 'html.parser')
    for link in soup.find_all("a", href=lambda href: href and "/recipes/" in href):
        if link not in recipe_urls:
            recipe_urls.append(link.get("href"))
print(recipe_urls)

headerList = ['name', 'description', 'nutrition_name', 'nutrition_value',
              'ingredients', 'method', 'recipe_url']
data = []
prog_bar = tqdm(total=len(recipe_urls))
prog_bar.set_description(f"Starting download")
for recipe in recipe_urls:
    recipe_url = base_url + recipe
    recipe_page = requests.get(recipe_url)
    recipe_ingredients = []
    soup = BeautifulSoup(recipe_page.content, 'html.parser')
    recipe_ingredients_p = soup.find(
        'div', class_='recipe-ingrediens w-richtext'
    ).find_all('p')
    for i in recipe_ingredients_p:
        recipe_ingredients.append(i.text)
    recipe_method_p = soup.find(
        'div', class_='recipe-method w-richtext'
    ).find_all('p')
    recipe_method = ''
    for i in range(len(recipe_method_p)):
        recipe_method += '. ' + recipe_method_p[i].text + '\n'
    recipe_title = soup.find('h1', class_='recipe-title').text
    prog_bar.set_description(f"Downloading {recipe_title}")
    recipe_desc = soup.find('div', class_='recipe-description').text
    data = [recipe_title, recipe_desc, None, None, recipe_ingredients,
            recipe_method, recipe_url]
    writer.writerow(data)
    prog_bar.update(1)

file.close()

#code to add header to csv file
# import pandas as pd
#
# # read contents of csv file
# file = pd.read_csv("studentfood.csv")
# print("\nOriginal file:")
# print(file)
#
# # adding header
# headerList = ['name', 'description', 'nutrition_name', 'nutrition_value','ingredients', 'method', 'recipe_url']
#
# # converting data frame to csv
# file.to_csv("studentfoodrecipe.csv", header=headerList, index=False)
#
#
#
