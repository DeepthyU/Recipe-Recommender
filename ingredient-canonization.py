"""Ingredient Canonization.

Figures out mappings of ingredients to canonical ingredient names for all
ingredients which appear in the recipes we scraped.
"""
from typing import Tuple, List
import re
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd


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
        "g", "grams", "grammes",
        "kg", "kilograms", "kilogrammes",
        "ml", "milliliters", "millilitres",
        "l", "liters", "litres",
        "tsp", "teaspoon",
        "tbsp", "tablespoon",
        "spoon",
        "cm", "centimeter", "centimetre",
        "m", "meter", "metre",
        "mm", "millimeter", "millimetre",
        "pinch",
        "of",
        "sprinkle",
        "to taste",
        "small", "medium", "large",
        "drizzle"
    ]
    # Turn it into a regex compatible string
    units = "|".join(units)

    word_numbers = ["one", "two", "three", "four", "five", "six", "seven",
                    "eight", "nine", "ten", "a few", "small", "medium", "large",
                    "sprinkle", "of", "drizzle", "to taste", "pinch"]

    # Turn it into a regex compatible string
    word_numbers = "|".join(word_numbers)

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
    regex_str = rf"^((\d+|{word_numbers})\s*-*\s*)*({units})*"
    regex_amt_matcher = re.compile(regex_str, re.IGNORECASE)

    end_of_amount_str = regex_amt_matcher.match(ingredient).end()

    return (ingredient[0:end_of_amount_str].strip(),
            ingredient[end_of_amount_str:].strip())


def ingredient_list_canonization(ingredient_list: List[str]) -> List[list]:
    """Takes a list and makes the appropriate triple for each ingredient.

    Args:
        ingredient_list: The list of ingredients to process

    Returns:
        A list of tuples where each tuple is shaped like
            (original_ingredient, processed_amount, canonical_name)
    """
    return [[ing, *ingredient_split(ing)] for ing in ingredient_list]


def main(data_dir: Path):
    # First find the recipe files
    recipe_files = list(data_dir.glob("**/*.pkl"))
    # For each recipe file
    for recipe_file in recipe_files:
        # Read the file
        df = pd.read_pickle(recipe_file)
        df["ingredients"] = df["ingredients"]\
            .apply(lambda row: ingredient_list_canonization(row))

        df.to_pickle(recipe_file.with_name(recipe_file.name + "_canonical"))


if __name__ == '__main__':
    args = parse_args()
    main(args.data_dir)
