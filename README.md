# Recipe Recommender
Knowledge Engineering Assignment- Group 7

## Dataset Generation

First, ensure that there is an available Neo4j instance running.
This instance can either exist locally or on a server, as long as you have write-access to it.

Data preparation consists of 2 steps:

1. Ensure that `substitutions.csv` and `nutrition.csv` are in the data directory `data/`.
2. Prepare database by running the `src/prepare_database.py` script. This script takes the following arguments:

| Argument     | Description                                                                              |
|--------------|------------------------------------------------------------------------------------------|
| `DATA_DIR`   | Path to the data directory to be used                                                    |
| `PORT`       | The port to be used to connect to the database                                           |
| `--uri`      | An optional argument for which URI where Neo4j is hosted on.  Defaults to the localhost. |
| `--user`     | User to authenticate as for Neo4j. Defaults to `neo4j`                                   |
| `--password` | Pasword to authenticate with for Neo4j. Defaults to `password`                           |

## Web Interface

The web interface is started by running `UI.py` in the `src/web-app` directory.




Source used in this project are:
| Data                         | Source                                                                  |
|------------------------------|-------------------------------------------------------------------------|
| Recipe source 1              | BBC Student Recipes collection [^1]                                     |
| Recipe source 2              | The Student Food Project [^2]                                           |
| Ingredient nutritional value | Kaggle dataset “Nutritional values for common foods and products”[^3]   |
| Ingredient alternatives      | Work on food substitutions from Loesch et al. [^4]                      |
| Nutritional requirements     | Weighing Success web calculator [^5]                                    |

[^1]:https://www.bbcgoodfood.com/search?q=recipes
[^2]:https://www.thestudentfoodproject.com/
[^3]:https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products
[^4]:https://github.com/MaastrichtU-IDS/healthy-food-subs
[^5]:https://www.weighing-success.com/NutritionalNeeds.html

