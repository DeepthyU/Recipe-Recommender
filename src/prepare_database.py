"""Prepare Database.

Prepares the database we need by scraping all the websites, preprocessing
them, then adding them to the neo4j graph database.

Assumptions prior to starting:
    1. The nutrition dataset is already placed in the data_dir
    2. The substitutions dataset is already placed in the data_dir
"""
from argparse import ArgumentParser
from pathlib import Path
import gensim.downloader as api

from preprocessing.clean_data import clean_data
from preprocessing.recipe_ingredient_embedding import embed_recipe_ingredients
from preprocessing.word_embedding import embed_canonical_ingredients
from scrapers.scrape_bbc import scrape_from_bbc
from scrapers.scrape_studentfood import scrape_from_studentfoodproject
from knowledge_graph.ingredients_to_graph import add_ingredients_to_graph
from knowledge_graph.recipes_to_graph import add_recipes_to_graph


def parse_args():
    p = ArgumentParser(description="Prepares the database for Recipe "
                                   "Recommender")
    p.add_argument("DATA_DIR", type=Path,
                   help="Path to the data dir to be used.")
    p.add_argument("PORT", type=str,
                   help="Port used to connect to the database")
    p.add_argument("--user", type=str, default="neo4j",
                   help="User to authenticate as for neo4j")
    p.add_argument("--password", type=str, default="password",
                   help="Password to authenticate with for neo4j")
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    data_dir = args.DATA_DIR

    # Assure that nutrition and substitutions dataset are available
    assert (data_dir / "nutrition.csv").exists(), \
        "Nutritions dataset could not be found."
    assert (data_dir / "substitutions.csv").exists(), \
        "Substitutions dataset could not be found."

    # First scrape the websites
    if not ((data_dir / "recipe_bbc.pkl").exists()
            or (data_dir / "recipe_bbc_embedded.pkl").exists()):
        # Then we need to scrape the bbc website
        print("Scraping BBC website...")
        scrape_from_bbc(args.DATA_DIR)
    else:
        print("BBC website already scraped.")

    if not ((data_dir / "studentfoodrecipe.pkl)").exists()
            or (data_dir / "studentfoodrecipe_embedded.pkl").exists()):
        # Then we need to scrape the student food project website
        print("Scraping The Student Food Project website...")
        scrape_from_studentfoodproject(args.DATA_DIR)
    else:
        print("Student Food Project website already scraped.")

    # We then embed all the ingredients
    if not ((data_dir / "recipe_bbc_embedded.pkl").exists()
            and (data_dir / "studentfoodrecipe_embedded.pkl").exists()):
        # Then we need to embed the ingredients in the recipes
        print("Getting embeddings for recipe ingredients...")
        embed_recipe_ingredients(args.DATA_DIR)
    else:
        print("Recipe ingredient embeddings found.")

    canonical_embed_path = data_dir / "canonical_ingredient_embeddings.gz"
    if not canonical_embed_path.exists():
        print("Embedding canonical ingredients")
        # Load pretrained GloVe model
        print("Loading pretrained GloVe model (this may take a while)...")
        model = api.load("glove-wiki-gigaword-300")
        print("Pretrained model loaded!")

        embed_canonical_ingredients(data_dir, canonical_embed_path, model)
    else:
        print("Canonical ingredient embeddings found.")

    # And clean up the data for the other scripts
    print("Cleaning data for scripts...")
    clean_data(data_dir)

    # Embed canonical ingredients

    print("Now committing changes to the database.")
    should_continue = False
    while not should_continue:
        user_input = input("Continue? (y/n) >> ")
        if user_input == "n":
            exit()
        elif user_input == "y":
            should_continue = True

    uri = f"bolt://localhost:{args.PORT}"

    print("Adding canonical ingredients to graph")
    add_ingredients_to_graph(data_dir, uri, args.user, args.password)
    print("Adding recipes to graph")
    add_recipes_to_graph(data_dir, uri, args.user, args.password)
