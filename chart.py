import streamlit as st
import pandas as pd
import math
import json
import requests
from pathlib import Path
import altair as alt

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
sex_split = False
filter_list = {}


#container = st.container(border=True)
c1 = col1.container(border=True)
c1.subheader ("Main indicators / countries selection")

# Initialize session state for the inputs
if 'selected_datasource' not in st.session_state:
    st.session_state.selected_datasource = indicators_list['Indicator.datasource'].unique()[0]
if 'selected_cat' not in st.session_state:
    st.session_state.selected_cat = indicators_list[indicators_list['Indicator.datasource'] == st.session_state.selected_datasource]['Indicator.area'].unique()[0]
if 'selected_ind' not in st.session_state:
    st.session_state.selected_ind = indicators_list[(indicators_list['Indicator.datasource'] == st.session_state.selected_datasource) & 
                                        (indicators_list['Indicator.area'] == st.session_state.selected_cat)]['Indicator.short_name'].unique()[0]

# Function to update the options for Type based on selected Category
def update_cat():
    st.session_state.selected_cat = indicators_list[indicators_list['Indicator.datasource'] == st.session_state.selected_datasource]['Indicator.area'].unique()[0]
    update_ind()

# Function to update the options for Item based on selected Type
def update_ind():
    st.session_state.selected_ind= indicators_list[(indicators_list['Indicator.datasource'] == st.session_state.selected_datasource) & 
                                        (indicators_list['Indicator.area'] == st.session_state.selected_cat)]['Indicator.short_name'].unique()[0]
    
# Create widgets for each layer of input
c1.pills(
    ''':green[**1/5 - Data from which datasource?**]''', 
    options = indicators_list['Indicator.datasource'].unique(), 
    key='selected_datasource',
    on_change=update_cat
)


c1.selectbox(
    ''':green[**2/5 Select a category**]''',
    options=indicators_list[indicators_list['Indicator.datasource'] == st.session_state.selected_datasource]['Indicator.area'].unique(),
    key='selected_cat',
    on_change=update_ind
)

c1.selectbox(
    ''':green[**3/5 Select an indicator**]''',
    options=indicators_list[(indicators_list['Indicator.datasource'] == st.session_state.selected_datasource) & 
               (indicators_list['Indicator.area'] == st.session_state.selected_cat)]['Indicator.short_name'].unique(),
    key='selected_ind'
)

source = st.session_state.selected_datasource
url_code = ''.join(indicators_list[indicators_list['Indicator.short_name'] == st.session_state.selected_ind]['Indicator_Code'].values[0])
measure = indicators_list[indicators_list['Indicator.short_name'] == st.session_state.selected_ind]['Indicator.short_name'].values[0]
ind_longtitle = indicators_list[indicators_list['Indicator.short_name'] == st.session_state.selected_ind]['Indicator.long_name'].values[0]

#source = indicators_list[indicators_list['Indicator.short_name'] == st.session_state.selected_ind]['Indicator.datasource'].values
# ---------------------------------------------------------------------------
# Filering countries based on their name
countries_WHOEURO = pd.read_csv(Path(__file__).parent/'data/countries_WHO_Euro.csv')               
countries_df = pd.DataFrame(countries_WHOEURO)

# Declare some useful functions.

@st.cache_data
def get_wb_data(url):
    # Fetch data from the World Bank API in JSON format
    response = requests.get(url)
    datalist = response.json()    
    
    print ("url WB-->", url_a)
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

def get_oecd_data(url):
    #Fetch data from OECD API in csv
        
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

def get_data_from_eurostat (url_code):
    import eurostat
    global filter_list, sex_split
 
    #getting dimensions and data as pandas df
    df = eurostat.get_data_df(url_code)
    cols = list(df.columns)

    #setting up filter string for unpivoting
    not_unique_col = []
    unpivot_string = []
    vars_string = []
    time_period = False

    #defining vars to unpivot
    for i in cols:
            if (df[i].nunique() >1) or (): 
                not_unique_col.append(i)

    for i in not_unique_col:
        if (time_period):
            unpivot_string.append(i)
        else:
            vars_string.append(i)
            if i[:3] == 'geo':
                time_period = True
                toberenamed = i 
            else:
                unique_values = df[i].unique()
                
                if i == 'sex':
                    sex_split = True
                else: 
                    filter_list[i] = unique_values.tolist()
                

    gdp_df = pd.melt (df, id_vars = vars_string, value_vars= unpivot_string, var_name='Year', value_name="Value")
    gdp_df = gdp_df.rename (columns = {toberenamed : 'Country Code'})
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
    return gdp_df

#depending on the datasource setting ISO3 as country code to match data
countries_df['Country Code'] = countries_df['Countries.code']

match source:
    case "OECD":
        url_a = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STE," + url_code +"/.M.LI...AA...H?startPeriod=2023-02&dimensionAtObservation=AllDimensions"
        url_b = "https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=" + url_code +"&df[ag]=OECD.ELS.HD"  
         
    case "WORLD BANK":
        url_a = "https://api.worldbank.org/v2/country/all/indicator/"+ url_code +"?format=json&per_page=20000"
        url_b = "https://data.worldbank.org/indicator/" + url_code
        gdp_df = get_wb_data(url_a)  
        
    case "EUROSTAT":
        url_b = "https://ec.europa.eu/eurostat/web/products-datasets/-/"+ url_code
        gdp_df = get_data_from_eurostat(url_code)
        countries_df['Country Code'] = countries_df['Countries.iso2']
    case _:
        c1.write ("No datasource selected")

countries_df = countries_df.set_index('Country Code')

c = gdp_df['Country Code'].unique()   
cc = pd.DataFrame(c, columns=['Country Code'])              

#extract only Countries data from WHO/EURO
countries = pd.merge (cc, countries_df, on="Country Code" )                    

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

c1.write ("")

from_year, to_year = c1.slider(
    ''':green[**4/5 - Which years are you interested in?**]''',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

if not len(countries):
    st.warning("Select at least one country")

selected_countries = c1.multiselect(
    ''':green[**5/5 - Which countries would you like to view?**]''',
    countries['Countries.short_name'])

filtered_countries = countries[countries['Countries.short_name'].isin(selected_countries)]
column_titles = filtered_countries.columns.tolist()
iso_acronyms = filtered_countries['Country Code'].tolist()
filter_criteria = {}

c2  = col2.container(border=True)

#panel for optional filters if any in the data source
if len(filter_list) > 0:
    print("len filter list", len(filter_list))
    
    c2.subheader ("Filtering dimensions...")    
    if sex_split: c2.write(":green[**- Sex disaggregation**]")
    
    #Filtering data with indicator-specific dimensions
    for key, values in filter_list.items():
        filter_criteria[key] = c2.selectbox(f':green[**Select a value for {key}**]', values)
elif sex_split: 
    c2.subheader ("Filtering dimensions...")    
    c2.write(":green[**- Sex disaggregation**]")

# Filter the data
filtered_gdp_df = gdp_df[
        (gdp_df['Country Code'].isin(iso_acronyms)) & (gdp_df['Year'] <= to_year) & (from_year <= gdp_df['Year'])
    ]

#aligning boxes
col1, col2 = st.columns(2)
c1 = col1.container(border=True)
c2 = col2.container(border=True)

if len(filtered_gdp_df)>0:
    data_to_chart = filtered_gdp_df
    
    #filtering based on previous selections
    for key, value in filter_criteria.items():
        # filter with dimensions criteria
        data_to_chart = data_to_chart[data_to_chart[key] == value]
        
    if sex_split:
        #drawing the chart for sex=F
        dtc = data_to_chart[(data_to_chart['sex'] == 'F')]
        chart = alt.Chart(dtc).mark_line(point=True).encode(
            x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
            y='Value:Q',
            color='Country Code:N',
            tooltip=['Year', 'Value', 'Country Code']
        ).properties().interactive()
        #Display the chart in Streamlit
        c1.header (measure + " - Sex = F")
        c1.altair_chart(chart, use_container_width=True)
        pivot_data = dtc.pivot_table(index="Country Code", columns="Year", values="Value")
        pivot_data = pivot_data.round(2)
        c1.header ("Data table - " + measure + " - Sex = F")   
        c1.write(pivot_data)

        #drawing the chart for sex=M
        dtc = data_to_chart[(data_to_chart['sex'] == 'M')]
        chart = alt.Chart(dtc).mark_line(point=True).encode(
            x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
            y='Value:Q',
            color='Country Code:N',
            tooltip=['Year', 'Value', 'Country Code']
        ).properties().interactive()
        #Display the chart in Streamlit
        c2.header (measure + " - Sex = M")
        c2.altair_chart(chart, use_container_width=True)
        pivot_data = dtc.pivot_table(index="Country Code", columns="Year", values="Value")
        pivot_data = pivot_data.round(2)
        c2.header ("Data table - " + measure + " - Sex = M")   
        c2.write(pivot_data)
    else:           
            #drawing the chart when sex is not a dimension
            chart = alt.Chart(data_to_chart).mark_line(point=True).encode(
            x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
            y='Value:Q',
            color='Country Code:N',
            tooltip=['Year', 'Value', 'Country Code']
            ).properties().interactive()
            #Display the chart in Streamlit
            st.header (ind_longtitle)
            st.altair_chart(chart, use_container_width=True) 
            pivot_data = data_to_chart.pivot_table(index="Country Code", columns="Year", values="Value")
            pivot_data = pivot_data.round(2)
            st.header ("Data table - " + measure)   
            st.write(pivot_data)
else:
    c1.write(":red[Select indicator and country... No data to display with this selection]")

col1, col2 = st.columns(2)
c1 = col1.container(border=False)
c1.html("<a href="+url_b+" target='_blank'>Data source</a>")         