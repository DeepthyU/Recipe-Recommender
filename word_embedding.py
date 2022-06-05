"""Word Embedding.

Contains functions used for word embeddings.
"""
import re
import string
from typing import List

import numpy as np
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
