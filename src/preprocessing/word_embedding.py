"""Word Embedding.

Contains functions used for word embeddings.
"""
import re
import string
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from gensim.models import KeyedVectors

PUNCTUATION_TABLE = str.maketrans('', '', string.punctuation)
WORD_SPLIT = re.compile(r"\w+")


def embed_ingredient_string(ingredient_str: str,
                            model: KeyedVectors) -> np.ndarray:
    """Calculates the embedding of a given ingredient string.

    Args:
        ingredient_str: The ingredient string to be embedded.
        model: The model with which to calculate the embedding.
    """
    # First split ingredient into a list of words, without punctuation
    ing_list = WORD_SPLIT.findall(ingredient_str.translate(PUNCTUATION_TABLE))
    # Calculate its average embedding
    return calculate_averaged_embedding(ing_list, model)


def match_canonical_name(embedding: np.ndarray,
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

    Args:
        embedding: The embedding of the ingredient to be matched
        name_vecs: The embeddings of canonical ingredients as a KeyedVectors
            object.

    References:
        "Automated Identification of Food Substitutes Using Knowledge Graph
            Embeddings". Loesch et al.
        "GloVe: Global Vectors for Word Representation". Pennington et al.
        <https://github.com/RaRe-Technologies/gensim-data>
    Returns:
        The canonical name or None
    """
    if embedding is not None:
        # Get the most similar word
        most_similar = name_vecs.similar_by_vector(embedding, topn=1)[0]
        if most_similar[1] > 0.8:
            return most_similar[0]
    # If embedding was None or the similarity < 0.8,
    return None


def calculate_averaged_embedding(ingredient: List[str],
                                 model: KeyedVectors) -> np.ndarray or None:
    """Calculates the averaged word embedding of a list of words.

    Embedding is calculated by the GloVe embedding of canonical ingredient
    names. Names which are multi-word have their embedding vectors averaged.

    Matching canonical ingredient names are calculated at runtime by finding the
    cosine similarity between an ingredient and all canonical ingredients and
    the maximum, if it has a value above 0.8, is used as the canonical name.

    We use the pretrained model glove-wiki-gigaword-300.

    References:
        "Automated Identification of Food Substitutes Using Knowledge Graph
            Embeddings". Loesch et al.
        "GloVe: Global Vectors for Word Representation". Pennington et al.
        <https://github.com/RaRe-Technologies/gensim-data>
    """
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
        vec = calculate_averaged_embedding(WORD_SPLIT.findall(name), model)
        if vec is not None:
            keyed_vectors.add_vector(name, vec)
    keyed_vectors.save(str(embedding_path))
    print("Named vectors calculated!")
    return keyed_vectors
