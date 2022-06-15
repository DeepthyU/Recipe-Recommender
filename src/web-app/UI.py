import collections
from math import ceil

import streamlit as st
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import sys
import csv

# sys.path.insert(1,'../nutritional_requirements')
from pandas import DataFrame


def get_df(results, columns):
    recipe_list = []
    for i in results.data():
        recipe_list.append([i[columns[0]], str(i[columns[1]])])
    df = pd.DataFrame(recipe_list, columns=columns)
    # print(df)
    return df


def calculate_nutritional_value(nut_list):
    nutritional_value = 0
    # print(nut_list)
    for i in range(len(nut_list)):
        try:
            if 'g' in nut_list[i]['i.amount']:
                amount = float(nut_list[i]['i.amount'].replace('g', ''))
            elif 'ml' in nut_list[i]['i.amount']:
                amount = float(nut_list[i]['i.amount'].replace('ml', ''))
            elif 'kg' in nut_list[i]['i.amount']:
                amount = float(nut_list[i]['i.amount'].replace('kg', '')) * 1000
            else:
                    amount = float(nut_list[i]['i.amount'])
        except:
            amount = 0
        nutritional_value += amount * (float(nut_list[i]['nv_rel.amount'].replace('g', ''))) / 100
        # print("nutritional_value", nutritional_value)
    return nutritional_value


def get_nutr_from_db(session, recipe_name, nutrient):
    query = """MATCH (recipe:Recipe)-[i:HAS_INGREDIENT]->(ing:Ingredient)-[ci:HAS_CANONICAL_NAME]\
                    ->(can:CanonicalIngredient)-[nv_rel:HAS_NUTRITIONAL_VALUE]->(nv:NutritionalValue{name: $nutrient }) \
                     WHERE recipe.name = $recipe_name \
                     RETURN i.amount, nv_rel.amount"""
    results = session.run(query, recipe_name=recipe_name, nutrient=nutrient)
    return results


def get_recipe_diff(recipe_nutr_dict, person_req_dict):
    recipe_diff = []
    for key in recipe_nutr_dict:
        print(key)
        recipe_diff.append(abs(recipe_nutr_dict[key] - person_req_dict[key]))
    return max(recipe_diff)


import nutritional_requirements.constants as const
from nutritional_requirements.person_profile import PersonProfile
from nutritional_requirements.nutrition_requirements import NutritionReq
from os.path import exists
from nutritional_requirements.compute import compute_nutritional_needs

st.title('Recipe recommendations for students')
st.subheader('To calculate your nutrition requirements, please enter your information below (metric unit)')
neo4j_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
session = neo4j_connection.session()
results = (session.run("MATCH p = (recipe:Recipe)-[i:HAS_INGREDIENT]->(ing:Ingredient)-\
                        [ci:HAS_CANONICAL_NAME]->(can:CanonicalIngredient) \
                        RETURN DISTINCT can.name"))
ingredient_list = [i[0] for i in (results.values())]

username = st.text_input('Enter username')
st.session_state['username'] = username
# get usernames from csv file
# check if csv file exists
header_true = True
if exists('user_details.csv'):
    header_true = False
    user_df = pd.read_csv('user_details.csv', index_col=0)
    user_list = list(user_df['Username'])
else:
    user_list = []
if st.session_state.username not in user_list:
    with st.form("my_form"):
        height = st.number_input('Height in cm', 0)
        weight = st.number_input('Weight in kg', 0)
        sex = st.selectbox('Select your sex', (const.SEX_FEMALE, const.SEX_MALE))
        age = st.number_input('Age in full years', 0)
        activity_level = st.selectbox('Select activity level', (const.ACTIVITY_LEVEL_INACTIVE, const.ACTIVITY_LEVEL_LOW,
                                                                const.ACTIVITY_LEVEL_MODERATE,
                                                                const.ACTIVITY_LEVEL_HIGH))
        waist_size = st.number_input('Waist size in cm', 0)
        expectation = st.selectbox('Select your weight goal', (const.EXPECTATION_GAIN, const.EXPECTATION_LOSE,
                                                               const.EXPECTATION_MAINTAIN))
        protein_percent = st.number_input('Percent of protein in diet', 0)
        carb_percent = st.number_input('Percent of carbs in diet', 0)
        fat_percent = st.number_input('Percent of fat in diet', 0)
        if protein_percent + carb_percent + fat_percent != 100:
            st.error('Percentages do not add up to 100')
        submitted = st.form_submit_button("Submit")
        if submitted:
            index_label = [username]
            pd.DataFrame({'Username': [username], 'Sex': [sex], 'Height': [height], 'Weight': [weight], 'Age': [age],
                          'Activity level': [activity_level],
                          'Waist size': [waist_size], 'Expectation': [expectation],
                          'Protein_percent': [protein_percent],
                          'Carb_percent': [carb_percent], 'Fat_percent': [fat_percent]}, index=index_label).to_csv(
                'user_details.csv',
                mode='a', header=header_true,
                index=True)
            st.write('Your data has been submitted')
    person = PersonProfile(1, username, age, sex, height, weight, 'metric', activity_level, waist_size, expectation,
                           protein_percent, carb_percent, fat_percent)
else:
    df = user_df.loc[username]
    person = PersonProfile(1, df['Username'], df['Age'], df['Sex'], df['Height'], df['Weight'], 'metric',
                           df['Activity level'],
                           df['Waist size'], df['Expectation'],
                           df['Protein_percent'], df['Carb_percent'], df['Fat_percent'])

nutrition_requirements = compute_nutritional_needs(person)
carbs, fat, protein = nutrition_requirements.carb_grams, nutrition_requirements.fat_grams / 4, \
                      nutrition_requirements.protein_grams

query_get_recipes = "MATCH (recipe:Recipe) return recipe.name, recipe.method"
all_recipes = (session.run(query_get_recipes))
all_recipes_df = get_df(all_recipes, ['recipe.name', 'recipe.method'])
print("all_recipes.data()", all_recipes.data())

query_get_recipes = 'MATCH p = (recipe:Recipe)-[i:HAS_INGREDIENT]->(ing:Ingredient)-[ci:HAS_CANONICAL_NAME]\
            ->(can_ing:CanonicalIngredient)\
            return  recipe.name, can_ing.name'

recipes = (session.run(query_get_recipes))
df_recipe = get_df(recipes, ['recipe.name', 'can_ing.name'])

selected_ingredients_list = st.multiselect('Select ingredients (start typing to filter options)', ingredient_list,
                                           default=None, key=None)
if st.button('Continue'):
    print("selected_ingredients", selected_ingredients_list)
    # recipe dict to keep count of recipes which have the most number of selected ingredients
    recipe_dict = dict()
    for i in selected_ingredients_list:
        print(i)
        print(df_recipe[df_recipe['can_ing.name'] == i]['recipe.name'])
        for j in df_recipe[df_recipe['can_ing.name'] == i]['recipe.name']:
            if j in recipe_dict:
                recipe_dict[j] += 1
            else:
                recipe_dict[j] = 1
    print(recipe_dict)
    # get the recipe with the most number of selected ingredients
    max_recipe = max(recipe_dict, key=recipe_dict.get)
    print(max_recipe)
    print(all_recipes_df[all_recipes_df['recipe.name'] == max_recipe])
    recipe_nutr_dict = {}
    print("protein, carbs, fat", protein, carbs, fat)
    # pick top 5 recipes with the most number of selected ingredients
    sorted_recipes = dict(sorted(recipe_dict.items(), key=lambda item: item[1], reverse=True))
    print(sorted_recipes)
    counter = 0
    recipe_nut_val= {}
    for i in sorted_recipes:
        if counter == 5:
            break
        else:
            counter += 1
            recipe_nutr_dict[i] = {'Protein': 0, 'Carbohydrates': 0, 'Total Fat': 0}
            for j in recipe_nutr_dict[i]:
                res = get_nutr_from_db(session, i, j)
                print(j)
                recipe_nutr_dict[i][j] = ceil(calculate_nutritional_value(res.data()))
            recipe_nut_val[i] = get_recipe_diff(recipe_nutr_dict[i],
                                                     {'Protein': protein, 'Carbohydrates': carbs, 'Total Fat': fat})
    print(recipe_nutr_dict)

    # get max difference in nutritional values
    min_diff_recipe = min(recipe_nut_val, key=recipe_nut_val.get)
    print(min_diff_recipe)
    # display the recipe with the min difference in nutritional values
    st.write(min_diff_recipe)
    st.write(all_recipes_df[all_recipes_df['recipe.name'] == min_diff_recipe])

