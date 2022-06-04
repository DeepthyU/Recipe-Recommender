import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import pandas as pd


def get_one_page(url):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/70.0.3538.25 '
                             'Safari/537.36 '
                             'Core/1.70.3777.400 '
                             'QQBrowser/10.6.4212.400'}
    url = url.strip()
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
            if (not href.startswith('/recipes/category/')
                    and not href.startswith('/recipes/collection/')):
                links.append(href)
    links = list(set(links))
    # print(links,len(links))
    return links


def parse_one_article(currenturl, link):
    if link is not None:
        soup = BeautifulSoup(link, 'lxml')
        name = soup.select(
            "#__next > div.default-layout > main > div > section > div > "
            "div.post-header__body.oflow-x-hidden > "
            "div.headline.post-header__title.post-header__title--masthead"
            "-layout > h1")[
            0].get_text()
        description = soup.select(
            "#__next > div.default-layout > main > div > section > div > "
            "div.post-header__body.oflow-x-hidden > "
            "div.editor-content.mt-sm.pr-xxs.hidden-print > p")[
            0].get_text()
        # prep_time=soup.select("#__next > div.default-layout > main > div >
        # section > div > div.post-header__body.oflow-x-hidden >
        # ul.post-header__row.post-header__planning.list.list--horizontal >
        # li > div > div.icon-with-text__children > ul > li > span > time")
        # cook_time=soup.select("#__next > div.default-layout > main > div >
        # section > div > div.post-header__body.oflow-x-hidden >
        # ul.post-header__row.post-header__planning.list.list--horizontal >
        # li > div > div.icon-with-text__children > ul > li > span > time")
        nutrition_names = soup.select(
            "#__next > div.default-layout > main > div > section > div > "
            "div.post-header__body.oflow-x-hidden > table > tbody > tr > "
            "td.key-value-blocks__key")
        nutrition_name = []
        for i in range(len(nutrition_names)):
            nutrition_name.append(nutrition_names[i].get_text())
        nutrition_values = soup.select(
            "#__next > div.default-layout > main > div > section > div > "
            "div.post-header__body.oflow-x-hidden > table > tbody > tr > "
            "td.key-value-blocks__value")
        nutrition_value = []
        for i in range(len(nutrition_values)):
            nutrition_value.append(nutrition_values[i].get_text())
        ingredient_list = soup.select(
            "#__next > div.default-layout > main > div > div > "
            "div.layout-md-rail > div.layout-md-rail__primary > "
            "div.post__content > div > div > "
            "section.recipe__ingredients.col-12.mt-md.col-lg-6 > section > ul "
            "> li")
        ingredients = []
        for i in range(len(ingredient_list)):
            ingredients.append(ingredient_list[i].get_text())
        methods = soup.select(
            "#__next > div.default-layout > main > div > div > "
            "div.layout-md-rail > div.layout-md-rail__primary > "
            "div.post__content > div > div > "
            "section.recipe__method-steps.mb-lg.col-12.col-lg-6 > div > ul > "
            "li > div > p")
        method = []
        for i in range(len(methods)):
            method.append('Step' + str(i + 1) + ': ' + methods[i].get_text())
        # name=['title','description','nutrition_name',' nutrition_value',
        # 'ingredients','recipe_url']
        data = {"name": name,
                "description": description,
                "nutrition_name": nutrition_name,
                "nutrition_value": nutrition_value,
                "ingredients": ingredients,
                "method": method,
                "recipe_url": currenturl}
        return 1, data
    return 0, None


def main():
    data = {"name": [],
            "description": [],
            "nutrition_name": [],
            "nutrition_value": [],
            "ingredients": [],
            "method": [],
            "recipe_url": []}
    # with open('../data/recipe_bbc.csv', 'w', encoding='utf-8-sig',
    #           newline='') as f:
    #     f.truncate(0)
    #     names = ["name", "description", "nutrition_name", "nutrition_value",
    #              "ingredients", "method", "recipe_url"]
    #     write = csv.writer(f, dialect='excel', delimiter=";")
    #     write.writerow(names)

    urls = [f"https://www.bbcgoodfood.com/search/recipes/page/" \
            f"{number}/?q=recipes&sort=-popular" for number in range(1, 81)]

    links = []

    links_file = Path("../data/bbc_recipe_urls.txt")
    if links_file.exists():
        print("Links file exists. Using prefetched links.")
        with open(links_file) as f:
            links = f.readlines()
    else:
        for url in tqdm(urls, desc="Collecting recipe urls"):
            page = get_one_page(url)
            for link in parse_one_page(page):
                links.append(f"https://www.bbcgoodfood.com{link}\n")
        with open(links_file, "w") as f:
            f.writelines(links)

    p_bar = tqdm(total=len(links), desc="Parsing recipes")
    for link in links:
        current_url = link
        page = get_one_page(current_url)
        count, recipe_data = parse_one_article(current_url, page)

        if recipe_data is not None:
            for key, value in recipe_data.items():
                data[key].append(value)
        else:
            p_bar.write("Invalid file")
        p_bar.update(1)

    data_df = pd.DataFrame(data)
    print(f"Collected {len(data_df)} recipes")
    data_df.to_pickle(str(Path("../data/recipe_bbc.pkl")))


if __name__ == '__main__':
    main()
