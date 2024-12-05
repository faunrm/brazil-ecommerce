import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import json
import requests
import plotly.graph_objects as go
import datetime as dt
import seaborn as sns
from babel.numbers import format_currency

drive_link = "https://drive.google.com/file/d/12MLfNHv_Y--RMvbCGMYcqzgr6VWxgXA1/view?usp=sharing"
file_id = drive_link.split('/d/')[1].split('/')[0]
download_url = f"https://drive.google.com/uc?id={file_id}"

response = requests.get(download_url)
csv_path = "all_df.csv"
with open(csv_path, "wb") as file:
    file.write(response.content)

all_df = pd.read_csv(csv_path)

olist_logo_path = 'olist_logo.png'

st.title("Brazillian e-Commerce Analysis :shopping_trolley:")


with st.sidebar:
  st.image(olist_logo_path)
  start_date, end_date = st.date_input(
        label='Time Interval',min_value=dt.date(2016, 1, 1),
        max_value=dt.date(2018, 12, 31),
        value=[dt.date(2016, 1,1),dt.date(2018, 12, 31)]
    )
  container = st.container()
  state_option = list(set(all_df.customer_state) | set(all_df.seller_state))
  state = st.multiselect("Select one or more state options:",state_option, state_option)
  all = st.checkbox("Select all", value=True)
  if not all:
    state = st.multiselect("Select one or more state options:",state_option)

main_df = all_df[(all_df['order_purchase_timestamp'] >= str(start_date)) & (all_df['order_purchase_timestamp'] <= str(end_date)) & ((all_df.customer_state.isin(state)) | (all_df.seller_state.isin(state)))]

st.header('A Glimpse of the Dataset')
st.text('This is a Brazilian ecommerce public dataset of orders made at Olist Store. The dataset has information of 100k orders from 2016 to 2018 made at multiple marketplaces in Brazil. Its features allows viewing an order from multiple dimensions: from order status, price, payment and freight performance to customer location, product attributes and finally reviews written by customers.')
st.write(main_df.head())

#Monthly Order
st.header('Order Information')

col1, col2 = st.columns(2)

with col1:
  total_order = main_df.order_id.nunique()
  st.metric("Total orders", value=total_order)

with col2:
  total_revenue = format_currency(round(main_df.price.sum(), 2), 'BRL', locale = 'pt_BR')
  st.metric("Total Revenue", value=total_revenue)

main_df['order_purchase_timestamp'] = pd.to_datetime(main_df['order_purchase_timestamp'], errors='coerce')
main_df['order_month'] = main_df['order_purchase_timestamp'].dt.to_period('M')
monthly_orders = main_df.groupby('order_month').agg({'order_id': 'count'}).reset_index()

x = monthly_orders['order_month'].astype(str)
y = monthly_orders['order_id'].to_numpy()

st.subheader('Monthly Order')
fig1, ax = plt.subplots(figsize=(60, 15))
sns.lineplot(x = x, y = y , ax = ax, marker = 'o', markersize = 18, linewidth=5, color="#171f54")
ax.tick_params(axis='x', labelsize=25)
ax.tick_params(axis='y', labelsize=40)
st.pyplot(fig1)

#Top 5 Category by Sales
st.header('Top and Bottom 5 Categories by Sales')
## Find Top 5 and Bottom 5
sales_category = main_df.groupby(by = ['product_category_name_english']).agg({'product_id': 'count'}).reset_index()
sales_category = sales_category.sort_values(by='product_id', ascending=False).reset_index(drop=True)
top_5_sales = sales_category.head(5)
bottom_5_sales = sales_category.tail(5).sort_values(by='product_id', ascending=True).reset_index(drop=True)
## Create Graph
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(60, 20))
colors = ['#171f54', '#6e7394', '#6e7394', '#6e7394','#6e7394']

sns.barplot(x = 'product_id',y = 'product_category_name_english',data = top_5_sales, ax = ax[0], palette = colors)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=80)
ax[0].tick_params(axis='y', labelsize=40)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x = 'product_id',y = 'product_category_name_english',data = bottom_5_sales, ax = ax[1], palette = colors)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=80)
ax[1].tick_params(axis='y', labelsize=40)
ax[1].tick_params(axis='x', labelsize=30)
st.pyplot(fig)

#Top Category by State
top_sales_state = all_df.groupby(by = ['customer_state','product_category_name_english']).agg(product_count = ('product_id','count')).reset_index()
top_sales_state.columns = top_sales_state.columns.str.strip()
top_sales_state = top_sales_state.rename(columns={'product_category_name_english': 'product_category_name'})
top_sales_state = top_sales_state.sort_values(by='product_count', ascending=False)
top_sales_state = top_sales_state.groupby('customer_state').head(1).reset_index(drop=True)
top_sales_state.head()

geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson_data = requests.get(geojson_url).json()


fig7 = px.choropleth(
    top_sales_state,
    geojson=geojson_data,
    locations='customer_state',
    featureidkey='properties.sigla',
    color='product_category_name',
    hover_name='customer_state',
    title='Top Category by State'
    )


fig7.update_geos(
    visible=True,
    showcountries=True,
    countrycolor="Black",
    showcoastlines=True,
    coastlinecolor="Gray",
    projection_scale=5,
    center={"lat": -14.235, "lon": -51.925},
    projection_type="mercator"
)

st.plotly_chart(fig7)

# Review Score Distribution
st.subheader('Review Score Distribution')

ship_vs_score = main_df[['order_id', 'review_score', 'order_purchase_timestamp', 'order_delivered_customer_date']]
ship_vs_score = ship_vs_score.dropna()
ship_vs_score['order_delivered_customer_date'] = pd.to_datetime(ship_vs_score['order_delivered_customer_date'])
ship_vs_score['order_purchase_timestamp'] = pd.to_datetime(ship_vs_score['order_purchase_timestamp'])

ship_vs_score['shipping_time'] = (ship_vs_score['order_delivered_customer_date'] - ship_vs_score['order_purchase_timestamp']).dt.days
ship_vs_score = ship_vs_score.drop_duplicates(subset='order_id', keep='first')[['order_id', 'shipping_time', 'review_score']]
corr_ship_review = round(ship_vs_score[['shipping_time', 'review_score']].corr().iloc[0, 1], 5)
st.metric("Correlation of Shipping Time vs Review Score", value=corr_ship_review)

review_score = main_df[['order_id', 'review_score']].drop_duplicates().groupby(by='review_score').agg({'order_id': 'count'}).reset_index()
review_score = review_score.sort_values(by='review_score', ascending=False)

fig2, ax = plt.subplots(figsize=(15,6))
score = review_score['review_score']
count = review_score['order_id']

ax.bar(score, count)
bar_labels = ['1', '2', '3', '4','5']
bar_colors = ['tab:red', 'tab:orange', 'yellow', '#43f015','#43b924']

ax.bar(score, count, label=bar_labels, color=bar_colors)

ax.legend(title='Stars')
st.pyplot(fig2)

st.header('Customers and Sellers Distribution')
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson_data = requests.get(geojson_url).json()

cust_df = pd.read_csv('data\cust_state_df.csv')
sellers_df = pd.read_csv('data\seller_state_df.csv')

customer_state_df = cust_df.groupby(by='customer_state').agg({'customer_unique_id': 'count'}).sort_values(by='customer_unique_id', ascending=False).reset_index()
customer_state_df['state_iso'] = 'BR-' + customer_state_df['customer_state']

seller_state_df = sellers_df.groupby(by='seller_state').agg({'seller_id': 'count'}).sort_values(by='seller_id', ascending=False).reset_index()
seller_state_df['state_iso'] = 'BR-' + seller_state_df['seller_state']

col1, col2 = st.columns(2)

with col1:
  seller_total = seller_state_df['seller_id'].sum()
  st.metric("Total Sellers", value=seller_total)
  fig = px.choropleth(
      seller_state_df,
      geojson=geojson_data,
      locations='seller_state',            
      featureidkey='properties.sigla',     
      color='seller_id',               
      hover_name='seller_state',
      title='Seller Distribution by State',
      color_continuous_scale="Viridis",
      range_color=(0, seller_state_df['seller_id'].max())
      )

  fig.update_geos(
      visible=True,
      showcountries=True,
      countrycolor="Black",
      showcoastlines=True,
      coastlinecolor="Gray",
      projection_scale=3,
      center={"lat": -14.235, "lon": -51.925},
      projection_type="mercator"
      )

  st.plotly_chart(fig)

with col2:
  cust_total = cust_df.customer_unique_id.nunique()
  st.metric("Total Customers", value=cust_total)
  fig2 = px.choropleth(
    customer_state_df,
    geojson=geojson_data,
    locations='customer_state',
    featureidkey='properties.sigla',
    color='customer_unique_id',
    hover_name='customer_state',
    title='Customer Distribution by State',
    color_continuous_scale="Viridis",
    range_color=(0, customer_state_df['customer_unique_id'].max())
    )

  fig2.update_geos(
      visible=True,
      showcountries=True,
      countrycolor="Black",
      showcoastlines=True,
      coastlinecolor="Gray",
      projection_scale=3,
      center={"lat": -14.235, "lon": -51.925},
      projection_type="mercator"
      )

  st.plotly_chart(fig2)
