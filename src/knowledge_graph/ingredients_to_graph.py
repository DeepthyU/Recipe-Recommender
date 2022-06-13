"""Ingredients to graph.

Converts all ingredients into their appropriate graph representations.
"""
from argparse import ArgumentParser
from pathlib import Path
from typing import List

import pandas as pd
from gensim.models import KeyedVectors
from neo4j import GraphDatabase, Driver
from tqdm import tqdm
from time import perf_counter


def parse_args():
    p = ArgumentParser()
    p.add_argument("DATA_DIR", type=Path,
                   help="Path to the data directory")
    p.add_argument("PORT", type=str,
                   help="Port used to connect to the database")

    return p.parse_args()


def add_all_canonical_ingredients(driver: Driver,
                                  embeddings: KeyedVectors):
    """Adds all canonical ingredients to the knowledge graph.

    Args:
        driver: The driver the transactions should be committed with.
        embeddings: The embeddings of the canonical ingredients
    """
    ingredients = []
    # Iterate through all ingredients that we have previously embedded
    for key, index in tqdm(embeddings.key_to_index.items(),
                           desc="Processing canonical ingredients"):
        ingredients.append({"name": key.strip(),
                            "node_id": f"ci_{index:05d}",
                            "embedding": embeddings.get_vector(key).tolist()})
    print("Adding canonical ingredients...")
    start = perf_counter()
    with driver.session() as session:
        run_str = """ UNWIND $ingredients as row
                      MERGE (a:CanonicalIngredient {name: row.name})
                      ON CREATE SET a.id =        row.node_id,
                                    a.embedding = row.embedding"""
        session.run(run_str, ingredients=ingredients)
    t = perf_counter() - start
    print(f"Done adding canonical ingredients. {t=:.3f}")


def add_all_ingredient_substitutions(driver: Driver,
                                     substitutions: List[tuple]):
    """Adds all ingredient substitution relationships.

    Args:
        driver: The driver the transactions should be committed with.
        substitutions: The proper ingredient substitutions in (from, to) format.
    """
    for substitution in tqdm(substitutions, desc="Adding substitutions"):
        with driver.session() as session:
            run_str = """MATCH (a:CanonicalIngredient),
                               (b:CanonicalIngredient)
                         WHERE a.name = $origin AND b.name = $target
                         CREATE (a)-[r:HAS_SUBSTITUTE]->(b)"""
            session.run(run_str,
                        origin=substitution[0].strip(),
                        target=substitution[1].strip())


def parse_substitutions(substitution_path: Path) -> List[tuple]:
    """Parses the substitution CSV file."""
    subs_df = pd.read_csv(substitution_path)
    substitutions = []
    for record in subs_df.to_dict("records"):
        origin = record["Food label"].strip()
        target = record["Substitution label"].strip()
        substitutions.append((origin, target))
    return substitutions


def add_all_nutritional_values(driver: Driver, nutrition_df: pd.DataFrame):
    """Adds all nutritional values in the nutrition dataframe."""
    # Select nutritional values we are interested in
    nv_name_map = {"calories": "Calories",
                   "total_fat": "Total Fat",
                   "saturated_fat": "Saturated Fat",
                   "carbohydrate": "Carbohydrates",
                   "sugars": "Sugars",
                   "fiber": "Fiber",
                   "protein": "Protein",
                   "sodium": "Sodium"}

    print("Adding nutritional value entities...")
    for idx, (key, value) in enumerate(nv_name_map.items()):
        with driver.session() as session:
            run_str = """MERGE (a:NutritionalValue {name: $name})
                         ON CREATE SET a.id = $node_id"""
            session.run(run_str,
                        name=value.strip(),
                        node_id=f"nv_{idx:05d}")

    # Then add all ingredient -> nutritional value relations
    nutrition = nutrition_df.to_dict("records")
    for record in tqdm(nutrition, desc="Adding ingredient nutritional values"):
        relations = []
        for key, value in nv_name_map.items():
            relations.append({"origin": record["name"],
                              "target": value.strip(),
                              "amount": record[key]})
        with driver.session() as session:
            run_str = """ UNWIND $relations as row
                          MATCH (a:CanonicalIngredient),
                                (b:NutritionalValue)
                          WHERE a.name = row.origin AND b.name = row.target
                          CREATE (a)-[r:HAS_NUTRITIONAL_VALUE 
                                      {amount: row.amount}]->(b) """
            session.run(run_str, relations=relations)


def add_ingredients_to_graph(data_dir: Path, uri: str, user: str,
                             password: str):
    """Adds the provided ingredients to the graph.

    Args:
        data_dir: Path to the data directory.
        uri: URI the database is currently hosted on
        user: The user to authenticate to the database with.
        password: The password to authenticate to the database with.
    """
    canonical_embed_path = data_dir / "canonical_ingredient_embeddings.gz"

    # Collect required data
    print("Collecting required data...")
    canonical_embeddings = KeyedVectors.load(str(canonical_embed_path))
    substitutions = parse_substitutions(data_dir / "substitutions.csv")
    nutrition_df = pd.read_csv(data_dir / "nutrition.csv")

    # Actually commit to the database
    driver = GraphDatabase.driver(uri, auth=(user, password))

    print("Starting transactions...")
    add_all_canonical_ingredients(driver, canonical_embeddings)
    add_all_ingredient_substitutions(driver, substitutions)
    add_all_nutritional_values(driver, nutrition_df)

    driver.close()
    print("Done!")


if __name__ == '__main__':
    args = parse_args()
    add_ingredients_to_graph(args.DATA_DIR,
                             uri=f"bolt://localhost:{args.PORT}",
                             user="neo4j",
                             password="password")
