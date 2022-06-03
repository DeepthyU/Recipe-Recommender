"""Ingredient Canonization.

Figures out mappings of ingredients to canonical ingredient names for all
ingredients which appear in the recipes we scraped.
"""
from typing import Tuple
import re


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
        "kg", "kilograms", "kilogrammes"
                           "ml", "mililiters", "mililitres",
        "l", "liters", "litres",
        "tsp", "teaspoon",
        "tbsp", "tablespoon",
        "spoon",
        "cm", "centimeter", "centimetre",
        "m", "meter", "metre",
        "mm", "milimeter", "milimetre",
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
    500 g sommething
    200-500g of something
    200g-500g something
    3 of something
    3 somethings
    """
    # Sorry
    regex_str = rf"^(?'amount'(\d+|{word_numbers})\s*-*\s*)*(?'unit'{units})*"
    regex_amt_matcher = re.compile(regex_str, re.IGNORECASE)

    end_of_amount_str = regex_amt_matcher.match(ingredient).end()

    return (ingredient[0:end_of_amount_str].strip(),
            ingredient[end_of_amount_str:].strip())
