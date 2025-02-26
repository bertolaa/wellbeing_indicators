import streamlit as st
import pandas as pd
import math
import json
import requests
from pathlib import Path
import altair as alt
import xlrd

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Well-being economy indicators',
    layout="wide",
)

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
    
    print (gdp_df.head())
    return gdp_df

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

def get_data_from_whoeurope (url_code):
    global filter_list, sex_split

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url_code, headers=headers)

    dt = response.json()
    #print ("JSON Response status reading WHO api", response.status_code)

    sex_split = False
    df_string = {}
    years = []
    values = []
    country_codes = []
    sex = []
    dim = []

    for i in (dt[0]['dimensions']):
        dim.append(i['code'])

    if ("SEX" in dim): sex_split = True
        
    for entry in dt[0]['data']:
        years.append(entry['dimensions']['YEAR'])
        values.append(entry['value']['numeric'])
        country_codes.append(entry['dimensions']['COUNTRY'])   
        df_string = {'Country Code': country_codes, 'Year': years, 'Value': values}

        if (sex_split): 
            sex.append(entry['dimensions']['SEX'])
            df_string.update ({'sex': sex})

    # Convert to DataFrame
    df = pd.DataFrame(df_string)

    #check whether dataset has disaggregation by sex
    if (sex_split):
        if (df['sex'].nunique() < 2): sex_split = False

    df_cleaned = df[ df['Country Code'] != '']
    gdp_df = df_cleaned.sort_values(by=['Country Code', 'Year'])
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
    return gdp_df

def get_data_from_OECD (url_code):
    global filter_list, sex_split

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url_code, headers=headers)
    
    print ("JSON Response status reading WHO api", response.status_code)

    dt = response.json()   
    
    df_string = {}
    years = []
    values = []
    country_codes = []
    sex = []
    dim = []

    for i in (dt[0]['SeriesKey']):
        dim.append(i['REF_AREA'])
    
    
    for entry in dt[0]['data']:
        years.append(entry['dimensions']['YEAR'])
        values.append(entry['value']['numeric'])
        country_codes.append(entry['dimensions']['COUNTRY'])   
        df_string = {'Country Code': country_codes, 'Year': years, 'Value': values}

        if (sex_split): 
            sex.append(entry['dimensions']['SEX'])
            df_string.update ({'sex': sex})

    # Convert to DataFrame
    df = pd.DataFrame(df_string)

    if (sex_split):
        if (df['sex'].nunique() < 2): sex_split = False

    df_cleaned = df[ df['Country Code'] != '']
    gdp_df = df_cleaned.sort_values(by=['Country Code', 'Year'])
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
    return gdp_df

##############################################################################################################
# Draw the actual page
# Set the title that appears at the top of the page.
##############################################################################################################

st.header(":green[Well-being economy indicators]")
st.write("_... a tool to visualize well-being data from public databases_")

# Populating variables on "indicators.xls" and "countries_WHO_Euro.csv" files
data_filename = Path(__file__).parent/'data/Indicators.xls'
indicators = pd.read_excel(data_filename)                 
indicators_df = pd.DataFrame(indicators)                
sex_split = False
filter_list = {}

countries_WHOEURO = pd.read_csv(Path(__file__).parent/'data/countries_WHO_Euro.csv')               
countries_df = pd.DataFrame(countries_WHOEURO)

#Picking ISO3 as country code to match data
countries_df['Country Code'] = countries_df['Countries.code']

mod = "Country Profile" 
options = ["Explore countries", "Country Profile"]    

mod = st.pills ("Select type of visualization", options) 

if ( mod == "Explore countries" ):
    # Two equal columns:
    col1, col2 = st.columns(2)

    #container = st.container(border=True)
    c1 = col1.container(border=True)
    c1.subheader ("Main indicators / countries selection")

    # Initialize session state for category/indicator/country inputs
    if 'selected_datasource' not in st.session_state:
        st.session_state.selected_datasource = indicators_df['Indicator.datasource'].unique()[0]
    if 'selected_cat' not in st.session_state:
        st.session_state.selected_cat = indicators_df[indicators_df['Indicator.datasource'] == st.session_state.selected_datasource]['Indicator.area'].unique()[0]
    if 'selected_ind' not in st.session_state:
        st.session_state.selected_ind = indicators_df[(indicators_df['Indicator.datasource'] == st.session_state.selected_datasource) & 
                                            (indicators_df['Indicator.area'] == st.session_state.selected_cat)]['Indicator.short_name'].unique()[0]

    # Function to update the options for Type based on selected Category
    def update_cat():
        st.session_state.selected_cat = indicators_df[indicators_df['Indicator.datasource'] == st.session_state.selected_datasource]['Indicator.area'].unique()[0]
        update_ind()

    # Function to update the options for Item based on selected Type
    def update_ind():
        st.session_state.selected_ind= indicators_df[(indicators_df['Indicator.datasource'] == st.session_state.selected_datasource) & 
                                            (indicators_df['Indicator.area'] == st.session_state.selected_cat)]['Indicator.short_name'].unique()[0]
       
    # Create widgets for each layer of input
    c1.pills(
        ''':green[**1/5 - Data from which datasource?**]''', 
        options = indicators_df['Indicator.datasource'].unique(), 
        key='selected_datasource',
        on_change=update_cat
    )

    c1.selectbox(
        ''':green[**2/5 Select a category**]''',
        options=indicators_df[indicators_df['Indicator.datasource'] == st.session_state.selected_datasource]['Indicator.area'].unique(),
        key='selected_cat',
        on_change=update_ind
    )

    c1.selectbox(
        ''':green[**3/5 Select an indicator**]''',
        options=indicators_df[(indicators_df['Indicator.datasource'] == st.session_state.selected_datasource) & 
                (indicators_df['Indicator.area'] == st.session_state.selected_cat)]['Indicator.short_name'].unique(),
        key='selected_ind'
    )

    source = st.session_state.selected_datasource
    url_code = ''.join(indicators_df[indicators_df['Indicator.short_name'] == st.session_state.selected_ind]['Indicator_Code'].values[0])
    measure = indicators_df[indicators_df['Indicator.short_name'] == st.session_state.selected_ind]['Indicator.short_name'].values[0]
    ind_longtitle = indicators_df[indicators_df['Indicator.short_name'] == st.session_state.selected_ind]['Indicator.long_name'].values[0]

    match source:
        case "OECD":
            url_a = "https://sdmx.oecd.org/public/rest/data/" + url_code
            url_b = "https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=" + url_code +"&df[ag]=OECD.ELS.HD"  
            gdp_df = get_data_from_OECD(url_a)
                    
        case "WORLD BANK":
            url_a = "https://api.worldbank.org/v2/country/all/indicator/"+ url_code +"?format=json&per_page=20000"
            url_b = "https://data.worldbank.org/indicator/" + url_code
            gdp_df = get_wb_data(url_a)  
            
        case "EUROSTAT":
            url_b = "https://ec.europa.eu/eurostat/web/products-datasets/-/"+ url_code
            gdp_df = get_data_from_eurostat(url_code)
            countries_df['Country Code'] = countries_df['Countries.iso2']
        
        case "WHO/Europe":
            url_a = "https://dw.euro.who.int/api/v3/Batch/Measures?codes="+ url_code
            url_b = "https://dw.euro.who.int/api/v3/Batch/Measures?codes="+ url_code
            gdp_df = get_data_from_whoeurope(url_a)
        
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
        
        c2.subheader ("Filter dimensions...")    
        if sex_split: c2.write(":green[**- Sex disaggregation**]")
        
        #Filtering data with indicator-specific dimensions
        for key, values in filter_list.items():
            filter_criteria[key] = c2.selectbox(f':green[**Select a value for {key}**]', values)
            
    elif sex_split: 
        c2.subheader ("Filter dimensions...")    
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
            #prep the chart for sex=F
            dtc = data_to_chart[(data_to_chart['sex'] == 'F') | (data_to_chart['sex'] == 'FEMALE')]
            chart = alt.Chart(dtc).mark_line(point=True).encode(
                x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
                y='Value:Q',
                color='Country Code:N',
                tooltip=['Year', 'Value', 'Country Code']
            ).properties().interactive()
            
            #Display the chart in Streamlit for SEX = F
            c1.header (measure + " - Sex = F")
            c1.altair_chart(chart, use_container_width=True)
            pivot_data = dtc.pivot_table(index="Country Code", columns="Year", values="Value").round(2)
            c1.header ("Data table - " + measure + " - Sex = F")   
            c1.write(pivot_data)

            #prep the chart for sex=M
            dtc = data_to_chart[(data_to_chart['sex'] == 'M')  | (data_to_chart['sex'] == 'MALE')]
            chart = alt.Chart(dtc).mark_line(point=True).encode(
                x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
                y='Value:Q',
                color='Country Code:N',
                tooltip=['Year', 'Value', 'Country Code']
            ).properties().interactive()
            
            #Display the chart in Streamlit
            c2.header (measure + " - Sex = M")
            c2.altair_chart(chart, use_container_width=True)
            pivot_data = dtc.pivot_table(index="Country Code", columns="Year", values="Value").round(2)
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
                st.subheader (ind_longtitle)
                st.altair_chart(chart, use_container_width=True) 
                pivot_data = data_to_chart.pivot_table(index="Country Code", columns="Year", values="Value").round(2)
                st.subheader ("Data table - " + measure)   
                st.write(pivot_data)
    else:
        c1.write(":red[Select indicator and country... No data to display with this selection]")

    col1, col2 = st.columns(2)
    c1 = col1.container(border=False)
    c1.html("<a href="+url_b+" target='_blank'>Data source</a>")         
    
###############################################################################################
# selected the mode Country Profile from the main page
elif (mod == "Country Profile"):
    col1, col2 = st.columns(2)
    c1 = col1.container(border=False)
   
    #country selection
    selected_country= c1.selectbox(
     ''':green[*For which country would you like to produce a report?**]''', countries_df['Countries.short_name'], index=None)

    filtered_countries = countries_df[countries_df['Countries.short_name'] == selected_country]       
    filter_criteria = {}
    filter_columns = {}
    iso_acronyms = filtered_countries['Country Code'].to_list()
    indi_df = indicators_df[indicators_df['Country_Profile'] == True]
    
    #By clicking the button we start the production of the Country profile
    if ((c1.button ("Produce Country profile")) & (selected_country != None)):
    
        a = "Indicators to be elaborated: " + str(len(indi_df)) + " - Country: " + selected_country 
        c1.subheader (a)
        
        #iterate all the indicators to be included in the report
        for index, row in indi_df.iterrows():
            iso_acronyms = filtered_countries['Country Code'].to_list()
            url_code = row['Indicator_Code']
            sexocc = {}
            
            #title of the indicator            
            c1.subheader (str(row['Indicator.datasource'])+ " - " +(str(row['Indicator.short_name'])))
            
            #getting data
            match row['Indicator.datasource']:
                case "OECD":
                    url_a = "https://sdmx.oecd.org/public/rest/data/" + url_code
                    url_b = "https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=" + url_code +"&df[ag]=OECD.ELS.HD"  
                    gdp_df = get_data_from_OECD(url_a)
                            
                case "WORLD BANK":
                    url_a = "https://api.worldbank.org/v2/country/all/indicator/"+ url_code +"?format=json&per_page=20000"
                    url_b = "https://data.worldbank.org/indicator/" + url_code
                    gdp_df = get_wb_data(url_a)  
                    
                case "EUROSTAT":
                    url_b = "https://ec.europa.eu/eurostat/web/products-datasets/-/"+ url_code
                    gdp_df = get_data_from_eurostat(url_code)
                    iso_acronyms = filtered_countries['Countries.iso2'].to_list()
                    url_a = url_b

                
                case "WHO/Europe":
                    url_a = "https://dw.euro.who.int/api/v3/Batch/Measures?codes="+ url_code
                    url_b = "https://dw.euro.who.int/api/v3/Batch/Measures?codes="+ url_code
                    gdp_df = get_data_from_whoeurope(url_a)
            
            from_year = gdp_df['Year'].min()
            to_year = gdp_df['Year'].max()

            filtered_gdp_df = gdp_df[
            (gdp_df['Country Code'].isin(iso_acronyms)) & (gdp_df['Year'] <= to_year) & (from_year <= gdp_df['Year'])]          
           
            if (len(filtered_gdp_df) > 0):
                filtered_gdp_df = filtered_gdp_df.dropna()         
                column_titles = filtered_gdp_df.columns.tolist()
                dims_lower = [dim.lower() for dim in column_titles]
                print (url_code, column_titles, dims_lower)
                dims2 = [dim for dim in column_titles if ((dim != 'Year') and (dim != 'Value'))]
            
                #dims_chart needed to draw dimensions lines in the chart
                print ('dims2 before', dims2)      
                if (len(dims2) > 1): dims2.remove("Country Code")
                print ('dims2 after', dims2)          
            
                dtc = filtered_gdp_df
                chart = alt.Chart(dtc).mark_line(point=True).encode(
                x=alt.X('Year:Q', axis=alt.Axis(format='d')),   
                y='Value:Q',
                color = "".join(dims2),                 
                tooltip=['Year', 'Value', 'Country Code']
                ).properties().interactive()
                        
                #Display the chart in Streamlit for each unique occurrence of dimension SEX
                c1.altair_chart(chart, use_container_width=True)
            
                pivot_data = pd.pivot_table(filtered_gdp_df, index= dims2, columns="Year", values="Value", aggfunc='sum').round(2)   
                c1.write (pivot_data)
                
            else: c1.write(":red[Data not available for this indicator]")
            
            
            c1.html("<a href=" + url_a + " target='_blank'>Data link...</a>")  
            c1.write ('*************************************************************')            
else:
    st.write ("Select to proceed...")              




#*********************************************************
            
            
