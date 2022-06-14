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
        if 'g' in nut_list[i]['i.amount']:
            amount = float(nut_list[i]['i.amount'].replace('g', ''))
        elif 'ml' in nut_list[i]['i.amount']:
            amount = float(nut_list[i]['i.amount'].replace('ml', ''))
        elif 'kg' in nut_list[i]['i.amount']:
            amount = float(nut_list[i]['i.amount'].replace('kg', '')) * 1000
        else:
            try:
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

# carbohydrates, fat and protein requirements


nutrition_requirements = compute_nutritional_needs(person)
carbs, fat, protein = nutrition_requirements.carb_grams / 4, nutrition_requirements.fat_grams / 4, \
                      nutrition_requirements.protein_grams / 4

query_get_recipes = "MATCH (recipe:Recipe) return recipe.name, recipe.method"
all_recipes = (session.run(query_get_recipes))
all_recipes_df = get_df(all_recipes, ['recipe.name', 'recipe.method'])
print("all_recipes.data()", all_recipes.data())

# # for each recipe, ingredient, calculate the number of protein
# for i in all_recipes_df['recipe.name']:
#     query_protein = 'MATCH (recipe:Recipe)-[i:HAS_INGREDIENT]->(ing:Ingredient)-[ci:HAS_CANONICAL_NAME]\
#                     ->(can:CanonicalIngredient)-[nv_rel:HAS_NUTRITIONAL_VALUE]->(nv:NutritionalValue{name: "Protein"})\
#                      RETURN recipe.name, ing.name, can.name, i.amount, nv_rel.amount'
#
#     protein = (session.run(query_protein))

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
    print(all_recipes_df[all_recipes_df['recipe.name']==max_recipe])
    #
    # query_protein = 'MATCH (recipe:Recipe)-[i:HAS_INGREDIENT]->(ing:Ingredient)-[ci:HAS_CANONICAL_NAME]\
    #                 ->(can:CanonicalIngredient)-[nv_rel:HAS_NUTRITIONAL_VALUE]->(nv:NutritionalValue{name: "Protein"}) \
    #                  WHERE recipe.name = $max_recipe \
    #                  RETURN i.amount, nv_rel.amount'
    #
    # protein_res = (session.run(query_protein, max_recipe=max_recipe))
    nutrition_dict = {'Protein':0, 'Carbohydrates': 0, 'Total Fat': 0}
    for i in nutrition_dict:
        res = get_nutr_from_db(session, max_recipe, i)
        nutrition_dict[i] = ceil(calculate_nutritional_value(res.data()))

    print(nutrition_dict)
    print("protein, carbs, fat",protein, carbs, fat)
    # for each recipe, calculate the number of carbs
    # for each recipe, calculate the number of fat
    # get the amount for each ingredient based on ingredient amount string
    # multiply each ingredient by the amount
    # Then aggregate sum it for each recipe
    # Then filter the recipes based on nutritional requirements
    # Then sort the recipes based on the sum of protein, carbs and fat

    # recipe_dict[df_recipe[df_recipe['can_ing.name'] == i]['recipe.name'].values[0]] += 1

    # print("recipe_dict", recipe_dict)
    # df_grouped['match_percent'] = df_grouped['can_ing.name'].apply(lambda x: len([]) / len(selected_ingredients_list))
    # get recipes which have ingredients in the selected list
