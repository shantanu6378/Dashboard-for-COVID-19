import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib as plt
import dash_daq as daq

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

vaccine = pd.read_csv(r'C:\Users\shant\OneDrive\Desktop\STAT 430\COVID-19_Vaccinations_in_the_United_States_Jurisdiction.CSV')
geo_usa = gpd.read_file(r'C:\Users\shant\OneDrive\Desktop\STAT 430\US Map\cb_2018_us_state_5m.shp')
geo_usa = geo_usa[['STUSPS', 'geometry']]

def slider_marks(mydate, divs = 30):
    result = {}
    for i, date in enumerate(mydate, 1):
        if (i%divs == 1):
            result[i] = str(date)
    result[i] = str(mydate[-1])
    return result


#Merging the vaccine data with US Map data
df = geo_usa.merge(vaccine,left_on='STUSPS', right_on = 'Location')

#num_list = np.arange(1, len(df['D2'].unique())+1)
date_order = {}
for i, j in enumerate(df['Date'].unique()[::-1], 1):
    date_order[j] = i
df['date_order'] = df['Date'].map(date_order)

df = df.rename(columns={"Administered_Dose1_Pop_Pct":"At least 1 dose", 'Series_Complete_Pop_Pct':'Fully Vaccinated'})

# Second data frame with vaccine data of county:
county = pd.read_csv(r'C:\Users\shant\OneDrive\Desktop\STAT 430\COVID-19_Vaccinations_in_the_United_States_County.csv')

date_order2 = {}
for i, j in enumerate(county['Date'].unique()[::-1], 1):
    date_order2[j] = i
county['date_order'] = county['Date'].map(date_order2)

county = county.rename(columns={"Administered_Dose1_Pop_Pct":"At least 1 dose", 'Series_Complete_Pop_Pct':'Fully Vaccinated'})

# Third data frame with county transmission data:
county_transmission = pd.read_csv(r'C:\Users\shant\OneDrive\Desktop\STAT 430\United_States_COVID-19_County_Level_of_Community_Transmission_as_Originally_Posted.csv', na_values = 'suppressed')
def date_modifier2(date):
    date = date.replace('/', '')
    return int(date[:4]+date[4:6]+date[6:])

county_transmission.sort_values(by = 'report_date', inplace = True)
date_order3 = {}
for i, j in enumerate(county_transmission['report_date'].unique(), 1):
    date_order3[j] = i
county_transmission['date_order'] = county_transmission['report_date'].map(date_order3)

county_transmission['cases_per_100K_7_day_count_change'] = county_transmission['cases_per_100K_7_day_count_change'].apply(lambda x: float(str(x).replace(',', '')))

# Generic code:
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1(
        children='COVID-19 US Tracker',
        style={
            'textAlign': 'center',
        }
    ),

    html.H3(
        children='This application was created as a project in STAT 430, UIUC to visualise the data regarding vaccination status in different states and counties as well as the transmission status using Time series plots. Select appropriate buttons to explore the data. It takes some time to update. Please have patience!',        style={
            'textAlign': 'center',
        }
    ),
    html.Div([
        html.Label('Select Vaccination Status'),
        dcc.RadioItems(
            id='Vaccination-Stage',
            options=[{'label': i, 'value': i} for i in ['At least 1 dose', 'Fully Vaccinated']],
            value='At least 1 dose',
            labelStyle={'display': 'inline-block'}
        ),
        
        dcc.Graph(id='us_map'),
        html.H3(
        children='US Map showing percentage of vaccinated population' , style={
            'textAlign': 'center',
        }),
        html.Label('Select Date'),
        dcc.Slider(
            id='date-slider_us',
            min=list(slider_marks(df['Date'].unique()[::-1]).keys())[0],
            max=list(slider_marks(df['Date'].unique()[::-1]).keys())[-1],
            value=list(slider_marks(df['Date'].unique()[::-1]).keys())[0],
            marks=slider_marks(df['Date'].unique()[::-1])
        )
    ]),
    html.Br(),
    html.Div([
        html.Div([
            html.Label('Select State'),
            dcc.Dropdown(
                id='state-select',
                options=[{'label': i, 'value': i} for i in county['Recip_State'].unique()],
                value='IL'
        )], style={'padding': 10, 'flex': 1}),
        html.Div([
            html.Label('Select Vaccination Status'),
            dcc.RadioItems(
                id='Vaccination_Status',
                options=[{'label': i, 'value': i} for i in ['At least 1 dose', 'Fully Vaccinated']],
                value='At least 1 dose',
                labelStyle={'display': 'inline-block'}
        )], style={'padding': 10, 'flex': 1}),
        html.Label('Select Date'),
        dcc.Slider(
            id='date-slider_state',
            min=list(slider_marks(county['Date'].unique()[::-1]).keys())[0],
            max=list(slider_marks(county['Date'].unique()[::-1]).keys())[-1],
            #value=list(slider_marks(county['Date'].unique()[::-1]).keys())[0],
            marks=slider_marks(county['Date'].unique()[::-1])
        )  
    ]),

    html.Div([
        dcc.Graph(id='state_map')
    ]),
    html.H3(
        children='State Map with County-wise data' , style={
            'textAlign': 'center',
        }),
    html.Div([
        html.Label('Select State'),
        dcc.Dropdown(
            id='state-name-select',
            options=[{'label': i, 'value': i} for i in county_transmission['state_name'].unique()],
            value='Illinois'
        ),
        html.Label('Select County'),
        dcc.Dropdown(
            id='county-select',
            value='None'
        ),
        html.Label('Use slider to update time series chart'),
        dcc.RangeSlider(
        id='my-range-slider',
        min=list(slider_marks(county_transmission['report_date'].unique()).keys())[0],
        max=list(slider_marks(county_transmission['report_date'].unique()).keys())[-1],
        value=[list(slider_marks(county_transmission['report_date'].unique()).keys())[0], list(slider_marks(county_transmission['report_date'].unique()).keys())[-1]],
        marks = slider_marks(county_transmission['report_date'].unique()),
        #handleLabel={"showCurrentValue": True,"label": "DATE"}
        ),
        
        html.H3(
        'Daily percentage positivity: 7-day moving average', style={
            'textAlign': 'center',
        }),
        dcc.Graph(id='Time-series1'),
        
        html.H3(
        'Daily new cases per 100k: 7-day moving average', style={
            'textAlign': 'center',
        }),
        dcc.Graph(id='Time-series2')
    ])
])

@app.callback(
    Output('date-slider_state', 'value'),
    Input('state-select', 'value'))
def set_county_options(selected_state):
    county_f = county[county['Recip_State'] == selected_state]
    b = county_f['Date'].unique()[::-1]
    return list(slider_marks(b).keys())[0]

@app.callback(
    Output('county-select', 'options'),
    Input('state-name-select', 'value'))
def set_county_options(selected_state):
    return [{'label': i, 'value': i} for i in county_transmission[county_transmission['state_name'] == selected_state]['county_name'].unique()]

@app.callback(
    Output('county-select', 'value'),
    Input('county-select', 'options'))
def set_county_value(available_options):
    return available_options[0]['value']

@app.callback(
    Output('us_map', 'figure'),
    Input('Vaccination-Stage', 'value'),
    Input('date-slider_us', 'value'),
    )
def update_figure(selected_stage_us, selected_date_us):
    # US Map with vaccination status:
    filtered_df_us = df[df['date_order'] == selected_date_us]
    
    fig1 = px.choropleth(locations = filtered_df_us['Location'], locationmode = 'USA-states', color = filtered_df_us[selected_stage_us], 
        scope = 'usa', labels={'At least 1 dose':'Percentage with at least 1 dose', 'Fully Vaccinated': 'Percentage of Fully Vaccinated'},
        hover_name = filtered_df_us['Location']
        )

    fig1.update_layout(transition_duration=500)
    
    return fig1

@app.callback(
    Output('state_map', 'figure'),
    Input('state-select', 'value'),
    Input('Vaccination_Status', 'value'),
    Input('date-slider_state', 'value'),
    )
def update_figure(selected_state, selected_stage, selected_date):
    # State map with vaccination status:
    df2 = county[(county['Recip_State']==selected_state) & (county['date_order']==selected_date)]

    fig2 = px.choropleth(df2, geojson=counties, locations='FIPS', color=df2[selected_stage],
                           scope="usa",color_continuous_scale="Viridis",
                           labels={'Series_Complete_Pop_Pct':'Percentage'},
                           hover_name = df2['Recip_County']
                          )
    fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    fig2.update_layout(transition_duration=500)
    
    return fig2

@app.callback(
    Output('Time-series1', 'figure'),
    Output('Time-series2', 'figure'),
    Input('state-name-select', 'value'), 
    Input('county-select', 'value'), 
    Input('my-range-slider', 'value'))
def update_figure(selected_state, selected_county, selected_range):
    # Line plots County-wise:
    df_county_f = county_transmission[(county_transmission['county_name'] == selected_county) & (county_transmission['state_name'] == selected_state)]
    df_county_f['report_date'] = df_county_f['report_date'].astype('datetime64[ns]')
    df_county_f = df_county_f.sort_values(by = 'report_date')
    df_county_f = df_county_f[(df_county_f['date_order']>= selected_range[0]) & (df_county_f['date_order']<= selected_range[1])]

    fig3 = px.line(df_county_f, x = 'report_date', y = 'percent_test_results_reported_positive_last_7_days', labels = {'report_date': 'Date', 'percent_test_results_reported_positive_last_7_days': 'Percentage positive test results'})
    
    fig3.update_layout(transition_duration=500)

    fig4 = px.line(df_county_f, x = 'report_date', y = 'cases_per_100K_7_day_count_change', labels = {'report_date': 'Date', 'cases_per_100K_7_day_count_change': 'No. of positive Cases per 100k'})

    fig4.update_layout(transition_duration=500)

    return fig3, fig4


if __name__ == '__main__':
    app.run_server(debug=True)
