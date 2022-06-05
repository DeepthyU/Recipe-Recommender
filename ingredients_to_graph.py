"""Ingredients to graph.

Converts all ingredients into their appropriate graph representations.
"""
from pathlib import Path
from typing import List

from gensim.models import KeyedVectors
import gensim.downloader as api
import pandas as pd
from word_embedding import calculate_averaged_embedding
from neo4j import GraphDatabase, Driver, Transaction, Session
import numpy as np


def embed_canonical_ingredients(data_dir: Path, embedding_path: Path,
                                model: KeyedVectors):
    """Gets the embedding of canonical ingredients.

    Args:
        data_dir: Path to the data directory.
        embedding_path: Path where the embedding should be saved.
        model: Model to use to embed.
    """
    # Open nutrition csv
    names = pd.read_csv(data_dir / "nutrition.csv", usecols=['name'])

    # Calculate the vector value of all name strings
    print("Calculating vector values of all canonical ingredients")
    keyed_vectors = KeyedVectors(300)
    for name in names["name"].tolist():
        vec = calculate_averaged_embedding(name.split(','), model)
        if vec is not None:
            keyed_vectors.add_vector(name, vec)
    keyed_vectors.save(str(embedding_path))
    print("Named vectors calculated!")
    return keyed_vectors


def add_all_canonical_ingredients(session: Session,
                                  embeddings: KeyedVectors):
    """Adds all canonical ingredients to the knowledge graph.

    Args:
        session: The session the transactions should be committed on.
        embeddings: The embeddings of the canonical ingredients
    """
    # First define the transaction function
    def create_canonical_ingredient(tx: Transaction, data: dict):
        """Creates a canonical ingredient entity in the graph database.

        Args:
            tx: The transaction to write with
            data: A dictionary containing the node id, name, and embedding.
        """
        name = data["name"]
        node_id = data["id"]
        embedding = data["embedding"]
        run_str = f"""MERGE (a:CanonicalIngredient {{name:"{name}"}})
                      ON CREATE SET a.id = "{node_id}"
                      ON CREATE SET a.embedding = {embedding}"""

        tx.run(run_str)

    # Now iterate through all ingredients that we have previously embedded
    for key, index in embeddings.key_to_index.items():
        data = {"name": key,
                "id": f"ci_{index:05d}",
                "embedding": embeddings.get_vector(key)}
        session.write_transaction(create_canonical_ingredient, data)


def add_all_ingredient_substitutions(session: Session,
                                     substitutions: List[tuple]):
    """Adds all ingredient substitution relationships.

    Args:
        session: The session the transactions should be committed on.
        substitutions: The proper ingredient substitutions in (from, to) format.
    """
    # First define the transaction function
    def create_substitution_relation(tx: Transaction, relation: tuple):
        """Creates a single ingredient substitution relation."""
        origin = relation[0]
        target = relation[1]
        run_str = f"""MATCH (a:CanonicalIngredient),
                            (b:CanonicalIngredient)
                      WHERE a.name = "{origin}" AND b.name = "{target}"
                      CREATE (a)-[r:HAS_SUBSTITUTE]->(b)"""
        tx.run(run_str)

    # Now iterate through all ingredient substitution strings
    for substitution in substitutions:
        session.write_transaction(create_substitution_relation, substitution)


def parse_substitutions(substitution_path: Path) -> List[tuple]:
    """Parses the substitution CSV file."""
    subs_df = pd.read_csv(substitution_path)
    substitutions = []
    for record in subs_df.to_dict("records"):
        origin = record["Food label"].strip()
        target = record["Substitution label"].strip()
        substitutions.append((origin, target))
    return substitutions


def add_all_nutritional_values(session: Session, nutrition_df: pd.DataFrame):
    """Adds all nutritional values in the nutrition dataframe."""
    def add_nutrition_entity(tx: Transaction, data: dict):
        """Adds a given nutritional value as an entity.

        Args:
            data: A dictionary containing keys [id, name]
        """
        node_id = data["id"]
        name = data["name"]
        run_str = f"""MERGE (a:NutritionalValue {{name:"{name}"}})
                      ON CREATE SET a.id = '{node_id}'"""
        tx.run(run_str)

    nutrition_value_names = nutrition_df.columns[3:]
    for idx, nutrition_value_name in enumerate(nutrition_value_names):
        session.write_transaction(add_nutrition_entity,
                                  {'id': idx, 'name': nutrition_value_name})




def main(data_dir: Path, uri: str, user: str, password:str):
    """Adds the provided ingredients and recipes to the graph.

    Args:
        data_dir: Path to the data directory.
    """
    canonical_embed_path = data_dir / "canonical_ingredient_embeddings.gz"
    if not canonical_embed_path.exists():
        # Load pretrained GloVe model
        print("Loading pretrained GloVe model...")
        model = api.load("glove-wiki-gigaword-300")
        print("Pretrained model loaded!")

        embed_canonical_ingredients(data_dir, canonical_embed_path, model)

    # Collect required data
    canonical_embeddings = KeyedVectors.load(str(canonical_embed_path))
    substitutions = parse_substitutions(data_dir / "substitutions.csv")
    nutrition_df = pd.read_csv(data_dir / "nutrition.csv")

    # Actually commit to the database
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session as session:
        add_all_canonical_ingredients(session, canonical_embeddings)
        add_all_ingredient_substitutions(session, substitutions)






if __name__ == '__main__':
    main(Path("data/"))
