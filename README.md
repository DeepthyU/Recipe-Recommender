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
