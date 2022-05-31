import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from tqdm import tqdm


def get_one_page(url):
    headers = {'user-agent':
               # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0)
               # Gecko/20100101 Firefox/84.0'}
               # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)
               # AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141
               # Safari/537.36'}
                   'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3777.400 '
                   'QQBrowser/10.6.4212.400'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


def parse_one_page(url):
    soup = BeautifulSoup(url, 'html.parser')
    # get all the links in this page
    hrefs = []
    for link in soup.findAll('a'):
        hrefs.append(link.get('href'))
    res = list(filter(None, hrefs))
    # print(res)
    # get all needed links
    links = []
    for href in res:
        if href.startswith('/recipes/'):
            if not href.startswith(
                    '/recipes/category/') and not href.startswith(
                    '/recipes/collection/'):
                links.append(href)
    links = list(set(links))
    # print(links,len(links))
    return links


def parse_one_article(currenturl, link):
    if (link != None):
        soup = BeautifulSoup(link, 'lxml')
        name = soup.select(
            "#__next > div.default-layout > main > div > section > div > div.post-header__body.oflow-x-hidden > div.headline.post-header__title.post-header__title--masthead-layout > h1")[
            0].get_text()
        description = soup.select(
            "#__next > div.default-layout > main > div > section > div > div.post-header__body.oflow-x-hidden > div.editor-content.mt-sm.pr-xxs.hidden-print > p")[
            0].get_text()
        # prep_time=soup.select("#__next > div.default-layout > main > div > section > div > div.post-header__body.oflow-x-hidden > ul.post-header__row.post-header__planning.list.list--horizontal > li > div > div.icon-with-text__children > ul > li > span > time")
        # cook_time=soup.select("#__next > div.default-layout > main > div > section > div > div.post-header__body.oflow-x-hidden > ul.post-header__row.post-header__planning.list.list--horizontal > li > div > div.icon-with-text__children > ul > li > span > time")
        nutrition_names = soup.select(
            "#__next > div.default-layout > main > div > section > div > div.post-header__body.oflow-x-hidden > table > tbody > tr > td.key-value-blocks__key")
        nutrition_name = []
        for i in range(len(nutrition_names)):
            nutrition_name.append(nutrition_names[i].get_text())
        nutrition_values = soup.select(
            "#__next > div.default-layout > main > div > section > div > div.post-header__body.oflow-x-hidden > table > tbody > tr > td.key-value-blocks__value")
        nutrition_value = []
        for i in range(len(nutrition_values)):
            nutrition_value.append(nutrition_values[i].get_text())
        ingredient_list = soup.select(
            "#__next > div.default-layout > main > div > div > div.layout-md-rail > div.layout-md-rail__primary > div.post__content > div > div > section.recipe__ingredients.col-12.mt-md.col-lg-6 > section > ul > li")
        ingredients = []
        for i in range(len(ingredient_list)):
            ingredients.append(ingredient_list[i].get_text())
        methods = soup.select(
            "#__next > div.default-layout > main > div > div > div.layout-md-rail > div.layout-md-rail__primary > div.post__content > div > div > section.recipe__method-steps.mb-lg.col-12.col-lg-6 > div > ul > li > div > p")
        method = []
        for i in range(len(methods)):
            method.append('Step' + str(i) + ': ' + methods[i].get_text())
        # name=['title','description','nutrition_name',' nutrition_value','ingredients','recipe_url']
        recipes = []
        recipes.append(name)
        recipes.append(description)
        recipes.append(nutrition_name)
        recipes.append(nutrition_value)
        recipes.append(ingredients)
        recipes.append(method)
        recipes.append(currenturl)
        # print(recipes)
        with open('../data/recipe_bbc.csv', 'a', encoding='utf-8-sig',
                  newline='') as f:
            write = csv.writer(f, dialect='excel', delimiter=";")
            write.writerow(recipes)
        return 1
    print("invalid!")
    return 0


def main():
    with open('../data/recipe_bbc.csv', 'w', encoding='utf-8-sig',
              newline='') as f:
        f.truncate(0)
        names = ["name", "description", "nutrition_name", "nutrition_value",
                 "ingredients", "method", "recipe_url"]
        write = csv.writer(f, dialect='excel', delimiter=";")
        write.writerow(names)

    urls = [{"https://www.bbcgoodfood.com/search/recipes/page/{}/?q=recipes&sort=-popular".format(number) for number in range(1, 81)}]

    print("collecting...")
    i = 0
    for url in urls:
        for oneurl in tqdm(url):
            oneurl = get_one_page(oneurl)
            links = parse_one_page(oneurl)
            for link in links:
                currenturl = "https://www.bbcgoodfood.com" + link
                link = get_one_page(currenturl)
                count = parse_one_article(currenturl, link)
                i = count + i
                # break
                # print("one receipe is finished!")
            print("one page is finished!")
            time.sleep(0.1)
        print("webiste", url, "is finished!")
    print("has collected", i, " receipes")


main()
