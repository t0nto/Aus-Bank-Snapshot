#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:56:37 2023

@author: tom
"""

import pandas as pd
from deta import Deta
from io import BytesIO
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bank Snapshot", page_icon="🇦🇺")
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

@st.cache_resource()
def load_data():
    deta_2 = Deta(st.secrets["deta_key"])
    deta_drive_2 = deta_2.Drive(st.secrets["deta_name"])
    open_connection = deta_drive_2.get('aus_bank_snapshot')
    read_content = open_connection.read()
    open_connection.close()
    aus_data = pd.read_parquet(BytesIO(read_content))
    return aus_data


def organic_aggregation(data, tag, grouping=["Domain"]):
    if tag != "Overall":
        data = data.query("User_Tags == @tag")
    tmax = data.p1_clicks.sum()
    master_organic_agg = data.groupby(by=grouping, sort=False).agg("sum").reset_index().sort_values(by="Monthly_Clicks", ascending=False, ignore_index=True)
    master_organic_agg["Average_Rank"] =  round(master_organic_agg[["p1_count", "p2_count", "p3_count", "p4_count", "p5_count", "p6_count", "p7_count", "p8_count", "p9_count", "p10_count"]].multiply([1,2,3,4,5,6,7,8,9,10]).sum(axis=1) / master_organic_agg["Top_10_Rankings"], 2)
    master_organic_agg["Pct_Rank_1"] = master_organic_agg["p1_count"] / master_organic_agg["Top_10_Rankings"]
    master_organic_agg["Market_Share"] = round((master_organic_agg["Monthly_Clicks"] / tmax) * 100, 2)
    return master_organic_agg

def organic_performance_chart(file, tag, num=10):
    file = organic_aggregation(file, tag)
    if "_" in tag:
        tag.replace("_", " ").title()
    data = file.head(num)[["Domain", "Average_Rank", "Market_Share", "Top_10_Rankings"]]
    fig = px.scatter(data, x="Average_Rank", y="Market_Share", color="Domain", size='Top_10_Rankings', title='Top ' + str(num) + ' Domains for ' + tag + " Keyword Set")
    fig.update_xaxes(autorange="reversed")
    return fig

st.title("Australian Bank Organic Performance Snapshot - June 2023")
st.subheader("by [Wells & Harris](https://www.wellsandharris.com)")
aus_data = load_data()
cats = ["Overall"] + list(aus_data.User_Tags.unique())
cats.remove("personal_loans")
tabs =  st.tabs([i.replace("_", " ").title() + " || " for i in cats])
slider = st.slider(label="Select the number of domains", min_value=10, max_value=50, value=10, step=5)
for i, tab in enumerate(tabs):
    with tab:
        chart_data = organic_aggregation(aus_data, tag=cats[i])
        st.plotly_chart(organic_performance_chart(aus_data, tag=cats[i], num=slider))
        st.write("The leader of the " +  cats[i].replace("_", " ") + " category is " + chart_data.Domain[0] + " with a market share of " 
                 + str(chart_data.Market_Share[0]) + "%. Completing the top 3 are " +  chart_data.Domain[1] +  " and " 
                 + chart_data.Domain[2]  
                 + " with market shares of " + str(round(chart_data.Market_Share[0]-chart_data.Market_Share[1],2)) 
                 + "% and " +  str(round(chart_data.Market_Share[0]-chart_data.Market_Share[2],2)) + "% less than the leader.")
        
st.divider() 
st.write("At Wells & Harris, we provide due diligence for your marketing spend through our data-driven research. See how we can help you make smarter marketing decisions today – [get in touch](https://www.wellsandharris.com)")
