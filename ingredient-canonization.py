"""Ingredient Canonization.

Figures out mappings of ingredients to canonical ingredient names for all
ingredients which appear in the recipes we scraped.
"""
from typing import Tuple, List
import re
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
from gensim.models import KeyedVectors
import gensim.downloader as api
import numpy as np
import string
from tqdm import tqdm

PUNCTUATION_TABLE = str.maketrans('', '', string.punctuation)


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
    fraction_codes = "[\u00BC-\u00BE]|[\u2150-\u215E]|\d/\d"

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


def match_canonical_name(ingredient: str,
                         model: KeyedVectors,
                         name_vecs: KeyedVectors) -> str or None:
    """Matches the closest canonical name.

    Matches the given ingredient to the closest name in the names dataframe
    using cosine similarity. Uses a threshold of 0.8 as the cutoff below which
    no canonical name is returned.

    Matching is done by the GloVe embedding of canonical ingredient names.
    Names which are multi-word have their embedding vectors averaged. Once a
    GloVe embedding has been calculated, the cosine similarity between all
    ingredients are calculated and the maximum, if it has a value above 0.8, is
    used as the canonical name.

    We use the pretrained model glove-wiki-gigaword-300.

    References:
        "Automated Identification of Food Substitutes Using Knowledge Graph
            Embeddings". Loesch et al.
        "GloVe: Global Vectors for Word Representation". Pennington et al.
        <https://github.com/RaRe-Technologies/gensim-data>

    Returns:
        The canonical name or None
    """
    # First split ingredient into a list of words, without punctuation
    ing_list = ingredient.translate(PUNCTUATION_TABLE).split(' ')
    # Calculate its average embedding
    embedding = calculate_averaged_embedding(ing_list, model)
    if embedding is not None:
        # Get the most similar word
        most_similar = name_vecs.similar_by_vector(embedding, topn=1)[0]
        if most_similar[1] > 0.8:
            return most_similar[0]
    # If embedding was None or the similarity < 0.8,
    return None


def ingredient_list_canonization(ingredient_list: List[str],
                                 model: KeyedVectors,
                                 name_vecs: KeyedVectors) -> List[list]:
    """Takes a list and makes the appropriate triple for each ingredient.

    Args:
        ingredient_list: The list of ingredients to process

    Returns:
        A list of tuples where each tuple is shaped like
            (original_ingredient, processed_amount, ingredient, canonical name)
    """
    split_ingredients = []
    for ing in ingredient_list:
        amount, ingredient_name = ingredient_split(ing)
        canonical_name = match_canonical_name(ingredient_name, model, name_vecs)
        split_ingredients.append([ing, amount, ingredient_name, canonical_name])

    return split_ingredients


def calculate_averaged_embedding(ingredient: List[str],
                                 model: KeyedVectors) -> np.ndarray or None:
    """Calculates the averaged word embedding of a list of words"""
    vectors = []
    for word in ingredient:
        try:
            vectors.append(model.get_vector(word.strip().lower()))
        except KeyError:
            pass
    if len(vectors) > 0:
        vectors = np.stack(vectors)
        return np.mean(vectors, axis=0)
    else:
        return None


def get_canonical_vectors(data_dir: Path, model: KeyedVectors):
    vector_path = data_dir / "name_vectors.gz"
    if not vector_path.exists():
        # Open nutrition csv
        names = pd.read_csv(data_dir / "nutrition.csv", usecols=['name'])

        # Calculate the vector value of all name strings
        print("Calculating vector values of all canonical ingredients")
        keyed_vectors = KeyedVectors(300)
        for name in names["name"].tolist():
            vec = calculate_averaged_embedding(name.split(','), model)
            if vec is not None:
                keyed_vectors.add_vector(name, vec)
        keyed_vectors.save(str(vector_path))
        print("Named vectors calculated!")
        return keyed_vectors
    else:
        print("Loading name vectors...")
        keyed_vectors = KeyedVectors.load(str(vector_path))
        print("Name vectors loaded!")
        return keyed_vectors


def main(data_dir: Path):
    # First find the recipe files
    recipe_files = []
    for file in data_dir.glob("*.pkl"):
        if not str(file).endswith("_canonical.pkl"):
            recipe_files.append(file)

    # Load pretrained GloVe model
    print("Loading pretrained GloVe model...")
    model = api.load("glove-wiki-gigaword-300")
    print("Pretrained model loaded!")

    # Get vectors of canonical ingredient names
    name_vecs = get_canonical_vectors(data_dir, model)

    # For each recipe file
    for recipe_file in recipe_files:
        # Read the file
        df = pd.read_pickle(recipe_file)
        df["ingredients"] = df["ingredients"]\
            .apply(lambda row: ingredient_list_canonization(row, model,
                                                            name_vecs))

        df.to_pickle(recipe_file.with_name(recipe_file.stem + "_canonical.pkl"))


if __name__ == '__main__':
    args = parse_args()
    main(args.data_dir)
