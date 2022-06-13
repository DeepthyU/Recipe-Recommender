"""Recipe Ingredient Embedding.

Figures out the embeddings for every ingredient that appears in the recipes.
"""
from typing import Tuple, List
import re
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
from gensim.models import KeyedVectors
import gensim.downloader as api
from preprocessing.word_embedding import embed_ingredient_string, \
    match_canonical_name


def parse_args():
    """Parses the command line arguments."""
    parser = ArgumentParser(
        description="Ingredient Canonization.\n"
                    "Figures out mappings of ingredients to canonical "
                    "ingredient names for all ingredients which appear in "
                    "the recipes we scraped."
    )
    parser.add_argument(
        "data_dir",
        type=Path,
        help="Path to the data directory."
    )
    return parser.parse_args()


def ingredient_split(ingredient: str) -> Tuple[str, str]:
    """Splits the given ingredient into the amount and ingredient.

    Takes in an ingredient from a recipe which may contain an amount and splits
    it into the amount specified and the actual ingredient specified.

    Args:
        ingredient: The ingredient string with amount

    Returns:
        A tuple where the first string is the amount and the second string is
            the ingreident.
    """
    # All possible units used in recipes
    units = [
        "g ", "grams", "grammes",
        "kg", "kilograms", "kilogrammes",
        "ml", "milliliters", "millilitres",
        "l ", "liters", "litres",
        "tsp", "teaspoon",
        "tbsp", "tablespoon",
        "spoon",
        "cm", "centimeter", "centimetre",
        "m ", "meter", "metre",
        "mm", "millimeter", "millimetre",
        "pinch",
        "of",
        "sprinkle",
        "to taste",
        "small", "medium", "large",
        "drizzle",
        "pint",
        "cup",
    ]
    # Turn it into a regex compatible string
    units = "|".join(units)

    word_qtys = ["one", "two", "three", "four", "five", "six", "seven",
                 "eight", "nine", "ten",
                 "a few", "around"
                 "small", "medium", "large",
                 "of", "sprinkle",  "drizzle", "to taste", "pinch", "handful",
                 "pack", "pot", "tub", "clove", "can"]

    # Turn it into a regex compatible string
    word_qtys = "|".join(word_qtys)

    # Fractions also have to be taken into account
    fraction_codes = r"[\u00BC-\u00BE]|[\u2150-\u215E]|\d/\d"

    # Structure used for ingredients
    # This is a multiline comment just so I can visualize what kind of regex I
    # need to build
    """
    500g of something
    500 g of something
    500g something
    500 g something
    200-500g of something
    200g-500g something
    3 of something
    3 somethings
    """
    # Sorry
    regex_str = rf"^((\d+|{word_qtys}|{fraction_codes})\s*-*\s*)*({units})*"
    regex_amt_matcher = re.compile(regex_str, re.IGNORECASE)

    end_of_amount_str = regex_amt_matcher.match(ingredient).end()
    amount = ingredient[0:end_of_amount_str].strip()
    ingredient = ingredient[end_of_amount_str:]

    # Check for parentheses and remove everything within them
    parentheses_regex = re.compile(r"\(.*\)|\[.*]")
    ingredient = parentheses_regex.sub("", ingredient)
    ingredient = ingredient.strip()

    return amount, ingredient


def embed_ingredient_list(ingredient_list: List[str],
                          model: KeyedVectors,
                          canonical_embeddings: KeyedVectors) -> List[dict]:
    """Takes a list of ingredients and makes the appropriate dictionaries.

    Args:
        ingredient_list: The list of ingredients to process.
        model: The model to use for the embedding.
        canonical_embeddings: The embeddings of the canonical ingredients as a
            KeyedVectors object.

    Returns:
        A list of dictionaries with keys [original_name, amount,
            ingredient_name, canonical_name, embedding]
    """
    split_ingredients = []
    for ing in ingredient_list:
        amount, ingredient_name = ingredient_split(ing)
        embedding = embed_ingredient_string(ingredient_name, model)
        closest_canonical = match_canonical_name(embedding,
                                                 canonical_embeddings)
        split_ingredients.append({
            "original_name": ing,
            "amount": amount,
            "ingredient_name": ingredient_name,
            "canonical_name": closest_canonical,
            "embedding": embedding})

    return split_ingredients


def embed_recipe_ingredients(data_dir: Path):
    # First find the recipe files
    recipe_files = []
    for file in data_dir.glob("*.pkl"):
        if not str(file).endswith("_canonical.pkl"):
            recipe_files.append(file)

    # Load pretrained GloVe model
    print("Loading pretrained GloVe model...")
    model = api.load("glove-wiki-gigaword-300")
    print("Pretrained model loaded!")

    canonical_embeddings = KeyedVectors.load(
        str(data_dir / "canonical_ingredient_embeddings.gz")
    )

    # For each recipe file
    for recipe_file in recipe_files:
        # Read the file and calculate the ingredient embeddings
        df = pd.read_pickle(recipe_file)
        df["ingredients"] = df["ingredients"]\
            .apply(lambda row: embed_ingredient_list(row, model,
                                                     canonical_embeddings))

        df.to_pickle(recipe_file.with_name(recipe_file.stem + "_embedded.pkl"))


if __name__ == '__main__':
    args = parse_args()
    embed_recipe_ingredients(args.data_dir)
