import pandas as pd
from pathlib import Path


def clean_data(data_dir: Path):
    """Cleans the data so that it can be easily added to the database."""
    recipes = []

    for file in data_dir.glob("*_embedded.pkl"):
        recipes.append(pd.read_pickle(file))

    recipes = pd.concat(recipes)

    only_recipes = recipes[["name", "recipe_url", "description", "method"]]
    only_recipes.to_csv(data_dir / "clean_datasets" / "recipes.csv",
                        index=False)

    name_list = []
    kcal_list = []
    fat_list = []
    saturates_list = []
    carbs_list = []
    sugars_list = []
    fibre_list = []
    protein_list = []
    salt_list = []
    for name, item in zip(recipes["name"].tolist(),
                          recipes['nutrition_value'].tolist()):
        if item is not None:
            if len(item) > 1:
                name_list.append(name)
                kcal_list.append(item[0])
                fat_list.append(item[1].strip('g'))
                saturates_list.append(item[2].strip('g'))
                carbs_list.append(item[3].strip('g'))
                sugars_list.append(item[4].strip('g'))
                fibre_list.append(item[5].strip('g'))
                protein_list.append(item[6].strip('g'))
                salt_list.append(item[7].strip('g'))
    val_dict = {
        "name": name_list, 'Calories': kcal_list, 'Total Fat': fat_list,
        'Saturated Fat': saturates_list, 'Carbohydrates': carbs_list,
        'Sugars': sugars_list, 'Fiber': fibre_list, 'Protein': protein_list,
        'Sodium': salt_list
    }

    nv_only = pd.DataFrame(val_dict)

    nv_only.to_csv(data_dir / "clean_datasets" / "values.csv", index=False)
