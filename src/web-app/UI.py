import streamlit as st
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import sys
import csv

# sys.path.insert(1,'../nutritional_requirements')
import nutritional_requirements.constants as const
from nutritional_requirements.person_profile import PersonProfile
from nutritional_requirements.nutrition_requirements import NutritionReq
from os.path import exists
from nutritional_requirements.compute import compute_nutritional_needs

st.title('Recipe recommendations for students')
st.subheader('To calculate your nutrition requirements, please enter your information below (metric unit)')
neo4j_connection = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))
session = neo4j_connection.session()
results = (session.run("MATCH (n:CanonicalIngredient) RETURN n.name"))
ingredient_list = [i[0] for i in (results.values())]

# if username = '' is submitted, then it will always show the details of that person, and won't allow new person to be added
# todo: maybe fix it
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
        # TODO: Add a unique check for username
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
if st.button('Continue'):
    selected_ingredients_list = st.multiselect('Select ingredients', ingredient_list, default=None, key=None)
    nutrition_requirements = compute_nutritional_needs(person)
    carbs, fat, protein = nutrition_requirements.carb_calories/4, nutrition_requirements.fat_calories/4, \
                          nutrition_requirements.protein_calories/4
    total_calories = nutrition_requirements.total_eer
    query_get_recipes = 'match (carbs:NutritionalValue{name: "Carbohydrates"}) <-[c:HAS_NUTRITIONAL_VALUE ]-(a:Recipe)-[p:HAS_NUTRITIONAL_VALUE]->(protein:NutritionalValue{name: "Protein"})\
                        match (fats:NutritionalValue{name: "Total Fat"}) <-[f:HAS_NUTRITIONAL_VALUE ]-(a:Recipe)-[:HAS_INGREDIENT]->(i:Ingredient)\
                        WHERE c.amount/(c.amount+p.amount+f.amount) >'+ str(carbs/total_calories)+ ' AND p.amount/(c.amount+p.amount+f.amount)  >'+ str(protein/total_calories) +' AND f.amount/(c.amount+p.amount+f.amount)  >'+ str(fat/total_calories) +\
                        ' return  i, a limit 10'
    print(query_get_recipes)
    recipes = (session.run(query_get_recipes))
    print([i[0] for i in (recipes.values())])
    print( carbs, fat, protein)
