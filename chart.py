import streamlit as st
import pandas as pd
import math
import json
import requests
from pathlib import Path
import altair as alt
import pandaSDMX as sdmx

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Well-being economy indicators',
    layout="wide",
)

# Draw the actual page
# Set the title that appears at the top of the page.

st.header(":green[Well-being economy indicators]")
st.write("_... a tool to visualize well-being data from public databases_")

# Two equal columns:
col1, col2 = st.columns(2)

# ---------------------------------------------------------------------------
# Selecting indicators based on their name
data_filename = Path(__file__).parent/'data/Indicators.csv'
indicators = pd.read_csv(data_filename)                 
indicators_list = pd.DataFrame(indicators)                

#container = st.container(border=True)
c1 = col1.container(border=True)

area= c1.selectbox(''':green[**1/4 - Select Category**]''', indicators_list['Indicator.area'].unique())
filtered_df = indicators_list[indicators_list['Indicator.area'] == area]
c1.write ("")

selected_ind = c1.selectbox(''':green[**2/4 - Select Indicator**]''', filtered_df['Indicator.short_name'])

url_code = indicators_list[indicators_list['Indicator.short_name'] == selected_ind]['Indicator_Code'].values[0]
measure = indicators_list[indicators_list['Indicator.short_name'] == selected_ind]['Indicator.short_name'].values[0]
source = indicators_list[indicators_list['Indicator.short_name'] == selected_ind]['Indicator.datasource'].values[0]

# Declare some useful functions.

@st.cache_data
def get_wb_data(url):
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

def get_oecd_data_sdmx (url):
    oecd = sdmx.Request("OECD")
    
    # Set out everything about the request in the format specified by the OECD API
    data = oecd.data(
        resource_id="PDB_LV",
        key="GBR+FRA+CAN+ITA+DEU+JPN+USA.T_GDPEMP.CPC/all?startTime=2010",
    ).to_pandas()

    dlist = pd.DataFrame(data).reset_index()
    dlist.head()
    
    # Extract relevant data
    years = []
    gdp_values = []
    country_codes = []

    for i, row in dlist.iterrows():
            years.append(row['TIME_PERIOD'])
            gdp_values.append(row['OBS_VALUE'])
            country_codes.append(row['REF_AREA'])
         
    oecd_data = pd.DataFrame({
        'Country Code': country_codes,
        'Year': years,
        'Value': gdp_values
    })
        
    MIN_YEAR = 1960
    MAX_YEAR = 2024

    # Convert years from string to integers
    oecd_data['Year'] = pd.to_numeric(oecd_data['Year'])
       
    return oecd_data


def get_oecd_data(url):
    #Fetch data from OECD API in csv
    #This uses caching to avoid having to fetch the data every time.

   #url = 'https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI/.M.LI...AA...H?&dimensionAtObservation=AllDimensions&format=jsondata'
    
   # url = Path(__file__).parent/'data/dati.csv'
    
    response = requests.get(url)
    if response.status_code == 200:
        try:""
           
        except json.JSONDecodeError:
            print("Error decoding JSON. Response content:", response.text)
    else:
        
        print(f"Error: {response.status_code}")
        print("offline file used")
        url = Path(__file__).parent/'data/dati.csv'
    
    data = pd.read_csv(url)
    dlist = pd.DataFrame(data)
    
    
    # Extract relevant data
    years = []
    gdp_values = []
    country_codes = []

    for i, row in dlist.iterrows():
        if row['Unit of measure'] == "Percentage of GDP":
            years.append(row['TIME_PERIOD'])
            gdp_values.append(row['OBS_VALUE'])
            country_codes.append(row['REF_AREA'])
         
    oecd_data = pd.DataFrame({
        'Country Code': country_codes,
        'Year': years,
        'Value': gdp_values
    })
        
    MIN_YEAR = 1960
    MAX_YEAR = 2024

    # Convert years from string to integers
    oecd_data['Year'] = pd.to_numeric(oecd_data['Year'])
       
    return oecd_data

match source:
    case "OECD":
        url_a = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STE," + url_code +"/.M.LI...AA...H?startPeriod=2023-02&dimensionAtObservation=AllDimensions"
        url_b = "https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=" + url_code +"&df[ag]=OECD.ELS.HD"  
         
        #https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI/.M.LI...AA...H?&dimensionAtObservation=AllDimensions&format=csvfilewithlabels
        gdp_df = get_oecd_data_sdmx (url_a)  
    case "WB":
        url_a = "http://api.worldbank.org/v2/country/all/indicator/"+ url_code +"?format=json&per_page=20000"
        url_b = "https://data.worldbank.org/indicator/" + url_code
        
        gdp_df = get_wb_data(url_a)  
    case _:
        c1.write ("No datasource selected")

#WB structure query
# http://api.worldbank.org/v2/country/all/indicator/+ url_code +"?format=json&per_page=20000"
# url_b = "https://data.worldbank.org/indicator/" + url_code

#OECD structure query
# https://sdmx.oecd.org/public/rest/dataflow/OECD.ELS.HD/DSD_SHA@DF_SHA_HK/1.0?references=all


# ---------------------------------------------------------------------------
# Selecting countries based on their name
data_filename = Path(__file__).parent/'data/countries_WHO_Euro.csv'
countries_exchange = pd.read_csv(data_filename)                                 #reading the csv
countries_df = pd.DataFrame(countries_exchange).set_index('Country Code')       #creates dataframe of WHO/EURO country names based on Country Code column
c = gdp_df['Country Code'].unique()                                             #creates list of countries from WB indicator based on unique Country Code
cc = pd.DataFrame(c,columns=['Country Code'])                                   #convert into a dataframe

countries = pd.merge (cc, countries_df, on="Country Code" )                     #extract only Countries data from WHO/EURO

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

c1.write ("")

from_year, to_year = c1.slider(
    ''':green[**3/4 - Which years are you interested in?**]''',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

if not len(countries):
    st.warning("Select at least one country")

selected_countries = c1.multiselect(
    ''':green[**4/4 - Which countries would you like to view?**]''',
    countries['Countries.short_name'])

filtered_countries = countries[countries['Countries.short_name'].isin(selected_countries)]
column_titles = filtered_countries.columns.tolist()
iso_acronyms = filtered_countries['Country Code'].tolist()

# Filter the data

filtered_gdp_df = gdp_df[
        (gdp_df['Country Code'].isin(iso_acronyms))
        & (gdp_df['Year'] <= to_year)
        & (from_year <= gdp_df['Year'])
    ]
c2  = col2.container(border=True)

if len(filtered_gdp_df)>0:
    c2.header( measure, divider='gray')
    
    # Create an Altair chart
    chart = alt.Chart(filtered_gdp_df).mark_line(point=True).encode(
        x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
        y='Value:Q',
        color='Country Code:N',
        tooltip=['Year', 'Value', 'Country Code']
    ).properties(
        
    ).interactive()

    # Display the chart in Streamlit
    c2.altair_chart(chart, use_container_width=True)

first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

def lastvalue():
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
                    label=f'{country} '+ ' - '+ measure,
                    value=f'{last_gdp:,.2f}',
                    delta=growth,
                    delta_color=delta_color
                )   
    else: st.write("Data or Country selection are missing")
    return

filtered_gdp_df

if len(filtered_gdp_df)>0:
    pivot_data = filtered_gdp_df.pivot_table(index="Country Code", columns="Year", values="Value")
    pivot_data = pivot_data.round(2)
    st.header ("Data table - " + measure)   
    pivot_data
    c2.html("<a href="+url_b+" target='_blank'>Data source</a>")
else: c2.write("Select indicator and country... No data to display with this selection")