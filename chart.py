import streamlit as st
import pandas as pd
import math
import requests
from pathlib import Path
import altair as alt

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Well-being economy indicators',
)

# Draw the actual page
# Set the title that appears at the top of the page.
st.header("WHO Venice - Well-being economy indicators")
st.subheader("_... a tool to visualize well-being data from public databases_")

# ---------------------------------------------------------------------------
# Selecting indicators based on their name
data_filename = Path(__file__).parent/'data/Indicators.csv'
indicators = pd.read_csv(data_filename)                 
indicators_list = pd.DataFrame(indicators)                

area= st.selectbox(''':blue[1/4 - Select Category]''', indicators_list['Indicator.area'].unique())
filtered_df = indicators_list[indicators_list['Indicator.area'] == area]

selected_ind = st.selectbox(''':blue[2/4 - Select Indicator]''', filtered_df['Indicator.short_name'])

url_code = indicators_list[indicators_list['Indicator.short_name'] == selected_ind]['Indicator_Code'].values[0]
measure = indicators_list[indicators_list['Indicator.short_name'] == selected_ind]['Indicator.short_name'].values[0]

url_a = "http://api.worldbank.org/v2/country/all/indicator/"+ url_code +"?format=json&per_page=20000"
url_b = "https://data.worldbank.org/indicator/" + url_code

# Declare some useful functions.

@st.cache_data
def get_gdp_data(url):
    """Fetch GDP data from the World Bank API.
    This uses caching to avoid having to fetch the data every time.
    """
    
    # Fetch data from the World Bank API in JSON format
    response = requests.get(url)
    datalist = response.json()
    
    # Extract relevant data
    years = []
    gdp_values = []
    country_codes = []

    for entry in datalist[1]:
        years.append(entry['date'])
        gdp_values.append(entry['value'])
        country_codes.append(entry['countryiso3code'])
 
    # Convert to DataFrame
    gdp_df = pd.DataFrame({
        'Country Code': country_codes,
        'Year': years,
        'Value': gdp_values
    })
        
    MIN_YEAR = 1960
    MAX_YEAR = 2024

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
       
    return gdp_df

gdp_df = get_gdp_data(url_a)

# ---------------------------------------------------------------------------
# Selecting countries based on their name
data_filename = Path(__file__).parent/'data/countries_WHO_Euro.csv'
countries_exchange = pd.read_csv(data_filename)                                 #reading the csv
countries_df = pd.DataFrame(countries_exchange).set_index('Country Code')       #creates dataframe of WHO/EURO country names based on Country Code column
c = gdp_df['Country Code'].unique()                                             #creates list of countries from WB indicator based on unique Country Code
cc = pd.DataFrame(c,columns=['Country Code'])                                   #convert into a dataframe

countries = pd.merge (cc, countries_df, on="Country Code" )                     #extract only Countries data from WHO/EURO

# Add some spacing
''

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    ''':blue[3/4 - Which years are you interested in?]''',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    ''':blue[4/4 - Which countries would you like to view?]''',
    countries['Countries.short_name'])

''
filtered_countries = countries[countries['Countries.short_name'].isin(selected_countries)]
column_titles = filtered_countries.columns.tolist()
iso_acronyms = filtered_countries['Country Code'].tolist()

# Filter the data

filtered_gdp_df = gdp_df[
        (gdp_df['Country Code'].isin(iso_acronyms))
        & (gdp_df['Year'] <= to_year)
        & (from_year <= gdp_df['Year'])
    ]


if len(filtered_gdp_df)>0:
    st.header( measure, divider='gray')
    # Create an Altair chart
    chart = alt.Chart(filtered_gdp_df).mark_line(point=True).encode(
        x=alt.X('Year:O', axis=alt.Axis(format='d')),  
        y='Value:Q',
        color='Country Code:N',
        tooltip=['Year', 'Value', 'Country Code']
    ).properties(
        
    ).interactive()

    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

cols = st.columns(4)

if len(selected_countries)>0:
    for i, country in enumerate(iso_acronyms):
        col = cols[i % len(cols)]

        with col:
            first_gdp = first_year[first_year['Country Code'] == country]['Value'].iat[0] 
            last_gdp = last_year[last_year['Country Code'] == country]['Value'].iat[0] 
            
            if math.isnan(first_gdp):
                growth = 'n/a'
                delta_color = 'off'
            else:
                growth = f'{last_gdp / first_gdp:,.2f}x'
                delta_color = 'normal'

            st.metric(
                label=f'{country} '+ measure,
                value=f'{last_gdp:,.2f}',
                delta=growth,
                delta_color=delta_color
            )   
    if len(filtered_gdp_df)>0:
        pivot_data = filtered_gdp_df.pivot_table(index="Country Code", columns="Year", values="Value")
        pivot_data = pivot_data.round(2)
        pivot_data 
    else: st.write("No data to display")
else: st.write("Country data are missing")

st.html("<a href="+url_b+" target='_blank'>Data source</a>")