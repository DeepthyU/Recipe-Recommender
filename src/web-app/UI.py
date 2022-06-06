import streamlit as st
import pandas as pd
import numpy as np
from neo4j import GraphDatabase

st.markdown(
    """
    <style>
    .reportview-container {
        background: url("https://images.app.goo.gl/LFCobouKtT7oZ7Qv7")
    }
   .sidebar .sidebar-content {
        background: url("https://images.app.goo.gl/LFCobouKtT7oZ7Qv7")
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('Recipe recommendations for students')
st.subheader('To calculate your nutrition requirements, please enter your information below')
height = st.number_input('Height in cm', 0)
weight = st.number_input('Weight in kg', 0)
age = st.number_input('Age in full years', 0)

neo4j_connection = GraphDatabase.driver(uri = "bolt://localhost:7687", auth=("neo4j", "password"))
session = neo4j_connection.session()
results = (session.run("MATCH (p:Ingredient) RETURN p.Name"))
ingredient_list = [i[0] for i in (results.values())]
st.multiselect('Select ingredients', ingredient_list, default=None, key=None)