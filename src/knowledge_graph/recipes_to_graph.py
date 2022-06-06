"""Recipes to graph.

Converts all recipes to their appropriate graph representations.
"""
from argparse import ArgumentParser
from pathlib import Path
from typing import List
import pandas as pd
from neo4j import Driver, GraphDatabase
from time import perf_counter
from tqdm import tqdm


def add_recipes(driver: Driver, recipe_df: pd.DataFrame):
    """Adds just the recipes to the graph."""
    recipes = []
    for idx, record in enumerate(recipe_df.to_dict("records")):
        record.update({"node_id": f"r_{idx:05d}"})
        recipes.append(record)

    print("Adding recipes...")
    start = perf_counter()
    with driver.session() as session:
        run_str = """ UNWIND $records as row
                      MERGE (a:Recipe {name: row.name})
                      ON CREATE SET a.id =          row.node_id
                      ON CREATE SET a.description = row.description
                      ON CREATE SET a.url =         row.recipe_url
                      ON CREATE SET a.method =      row.method """
        session.run(run_str, records=recipes)
    t = perf_counter() - start
    print(f"Done adding recipes. {t=:.3f}")


def add_recipe_nutritional_values(driver: Driver, nv_df: pd.DataFrame):
    """Adds relationships for recipe nutritional values to the graph."""
    records = nv_df.to_dict("records")

    nv_types = list(nv_df.columns)[1:]  # Ignore name

    for record in tqdm(records, desc="Adding recipe nutritional values"):
        relations = []
        for nv_type in nv_types:
            relations.append({"origin": record["name"],
                              "target": nv_type,
                              "amount": record[nv_type]})

        with driver.session() as session:
            run_str = """ UNWIND $relations as row
                          MATCH (a:Recipe),
                                (b:NutritionalValue)
                          WHERE a.name = row.origin AND b.name = row.target
                          CREATE (a)-[r:HAS_NUTRITIONAL_VALUE 
                                      {amount: row.amount}]->(b) """
            session.run(run_str, relations=relations)


def add_recipe_ingredients(driver: Driver, recipe_df: pd.DataFrame):
    """Adds associated ingredients to recipes on the graph."""
    # Make sure that the embeddings are a list
    def embeddings_to_list(ingredient_list):
        l = []
        for ingredient in ingredient_list:
            if ingredient["embedding"] is not None:
                e = (ingredient["embedding"].tolist())
            else:
                e = None
            l.append({'name': ingredient["original_name"],
                      "embedding": e})
        return l
    recipe_df["ingredients"] = recipe_df["ingredients"].apply(
        lambda x: embeddings_to_list(x))
    records = recipe_df.to_dict("records")

    for record in tqdm(records, desc="Adding recipe ingredients"):
        # Add the ingredients first
        with driver.session() as session:
            run_str = """ UNWIND $ingredients as row
                          MERGE (a:Ingredient {name: row.name})
                          ON CREATE SET a.embedding = row.embedding """
            session.run(run_str, ingredients=record["ingredients"])

        # Now make the relationships
        relations = []
        for ingredient in record["ingredients"]:
            relations.append({"origin": record["name"],
                              "target": ingredient["name"]})
        with driver.session() as session:
            run_str = """ UNWIND $relations as row
                          MATCH (a:Recipe),
                                (b:Ingredient)
                          WHERE a.name = row.origin AND b.name = row.target
                          CREATE (a)-[r:HAS_INGREDIENT]->(b) """
            session.run(run_str, relations=relations)



def add_recipes_to_graph(data_dir: Path, uri: str, user: str, password: str):
    """Adds the provided recipes to the graph.

    Args:
        data_dir: Path to the data directory.
        uri: URI the database is currently hosted on
        user: The user to authenticate to the database with.
        password: The password to authenticate to the database with.
    """
    recipe_df = pd.read_csv(data_dir / "clean_datasets" / "recipes.csv")
    nv_df = pd.read_csv(data_dir / "clean_datasets" / "values.csv")

    bbc_df = pd.read_pickle(data_dir / "recipe_bbc_embedded.pkl")
    sfp_df = pd.read_pickle(data_dir / "studentfoodrecipe_embedded.pkl")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    add_recipes(driver, recipe_df)
    add_recipe_nutritional_values(driver, nv_df)
    add_recipe_ingredients(driver, bbc_df)
    add_recipe_ingredients(driver, sfp_df)
