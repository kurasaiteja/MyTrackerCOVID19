import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import datetime
import numpy as np 
import pandas as pd 
import plotly as py
import plotly.express as px
import plotly.graph_objs as go
import geopandas as gpd
import json
from plotly.subplots import make_subplots
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import requests
from bs4 import BeautifulSoup
import dash_bootstrap_components as dbc

start_time = time.time();
url = 'https://www.mohfw.gov.in'
page = requests.get(url)

soup = BeautifulSoup(page.content, 'html.parser')

tbl = soup.find("table",{"class":"table table-striped"})

df = pd.read_html(str(tbl))[0]
print("--- %s seconds --- REQUESTS" % (time.time() - start_time))
df=df.iloc[:-3]
df.drop(columns="S. No.", inplace=True)
df.drop([16,22])
df = df.rename(columns={'Name of State / UT':'State'})
df = df.rename(columns={'Total Confirmed cases (Including 77 foreign Nationals)':'Confirmed'})
df = df.rename(columns={'Cured/Discharged/Migrated':'Recovered'})
df['Confirmed'] = df['Confirmed'].astype('int64')
df['Recovered'] = df['Recovered'].astype('int64')
df['Death'] = df['Death'].astype('int64')
df.replace(to_replace ="Telengana", 
                 value ="Telangana", inplace=True) 
df = df.sort_values(by="Confirmed",ascending=False)



Confirmed = df['Confirmed'].sum()
Recovered = df['Recovered'].sum()
Deaths = df['Death'].sum()
Active = Confirmed - Recovered - Deaths



#Reading the shape file
fp = "./Igismap/Indian_States.shp"
map_df = gpd.read_file(fp)


#Cleaning the Shape File
map_df.replace(to_replace ="Andaman & Nicobar Island", 
                 value ="Andaman and Nicobar Islands", inplace=True) 
map_df.replace(to_replace ="Arunanchal Pradesh", 
                 value ="Arunachal Pradesh", inplace=True)
map_df.replace(to_replace ="NCT of Delhi", 
                 value ="Delhi", inplace=True) 
map_df.replace(to_replace ="Chhattisgarh", 
                 value ="Chhattisgarh", inplace=True) 
map_df.replace(to_replace ="Jammu & Kashmir", 
                 value ="Jammu and Kashmir",inplace=True) 
map_df.drop([6,7,16,22,27],inplace=True)
#converting shx to json for chrolopleth
merged_json = json.loads(map_df.to_json())
#Convert to String like object.
json_data = json.dumps(merged_json)


fig = px.choropleth(df, geojson=merged_json, color="Confirmed",
                    locations="State", featureidkey="properties.st_nm",
                    color_continuous_scale = ["#ffffb2","#fecc5c","#fd8d3c","#f03b20","#bd0026"],
                    hover_name = "State",
                    projection="mercator"
                   )
fig.update_geos(fitbounds="locations", visible=False)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

##Line plot

df_india = pd.read_csv("./covid_19_india.csv")

df_india.replace(to_replace ="Telengana", 
                 value = "Telangana", inplace=True) 

date_values= df_india[df_india["State/UnionTerritory"]=="Telangana"].iloc[:,1]
confirmed_values= df_india[df_india["State/UnionTerritory"]=="Telangana"].iloc[:,8]
deaths_values=df_india[df_india["State/UnionTerritory"]=="Telangana"].iloc[:,7]
recovered_values=df_india[df_india["State/UnionTerritory"]=="Telangana"].iloc[:,6]

figline = go.Figure()
figline.add_trace(go.Scatter(x=date_values, y=confirmed_values,
                    mode='lines+markers',name='confirmed cases'
                   ))
figline.add_trace(go.Scatter(x=date_values, y=deaths_values,
                    mode='lines+markers',name='no. of deaths'
                    ))
figline.add_trace(go.Scatter(x=date_values, y=recovered_values,
                    mode='lines+markers',name='recovered cases'))
figline.update_yaxes(tick0=0, dtick=50) #Scaling Y-axis
figline.update_layout(
    title="StateWise- COVID-19 Analysis",
    xaxis_title="Day",
    yaxis_title="No. of people"
)


# Code for data table
def generate_table(dataframe, max_rows=30):
    table = dbc.Table.from_dataframe(dataframe, striped=True, bordered=True, hover=True)
    return table;

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ])

server = app.server

app.layout = html.Div(children=[
    html.H1(children='Stats of Covid19 India'),
    html.Div(children=[
    html.Div(className="divleft", children=[
        html.Div(className="det red", children=[
            html.H5(children="Confirmed"),
            html.H6(children = Confirmed)
            ]),
          html.Div(className="det green", children=[
            html.H5(children="Recovered"),
            html.H6(children = Recovered)
            ]),
           html.Div(className="det grey", children=[
            html.H5(children="Deaths"),
            html.H6(children = Deaths)
            ]),
           html.Div(children=[
             generate_table(df)
            ]),
        
    ]),
    html.Div(className="divright", children =[
        html.H3(className="MapHeader", children="India Map"),
        html.H6(className="MapContent", children="(Hover/tap to know details)"),
        html.Div(children=[
            html.H6(className="red", children=" Confirmed -    ", style={"display":"inline", "color":"#ff073a"}),
            html.H6(id="red",style={"display":"inline"}),
            html.H6(className="green", children=" Recovered -    ", style={"display":"inline","marginLeft":"2rem","color": "#28a745"}),
            html.H6(id="green",style={"display":"inline"}),
            html.H6(className="grey", children=" Deaths -    ", style={"display":"inline","marginLeft":"2rem","color": "#6c757d"}),
            html.H6(id="grey",style={"display":"inline"}),
              html.H3(id="state"),
            ]),
        html.Div(className="MapIndia", children=[
        html.Div(id='text-content'),
        dcc.Graph(
         id='map',
         figure = fig,
         config = {'displayModeBar': False,'scrollZoom': False}
        ),
        ]),
        html.Div(className="Linediv", children=[
            html.H3(className="MapHeader", children="Spread Trends"),
            html.H6(className="MapContent", children="(Hover/Tap on dots to see daily report)",style={"marginBottom":"3rem"}),
    html.P([
                    html.Label("Choose a State"),
                    dcc.Dropdown(id = 'opt', options=[
        {'label': i, 'value': i} for i in df.State.unique()
    ],
                                value = "Telangana")
                        ], style = {'width': '200px',
                                    'fontSize' : '20px',
                                    'display': 'inline-block'}),
    ]),
    dcc.Graph(id="plot", figure=figline)
    ])
    ]),
    
])
@app.callback([Output('red', 'children'),
    Output('green', 'children'),
    Output('grey', 'children'),
    Output('state', 'children')],
    [Input('map', 'hoverData')])
def update_text(hoverData):
    print(hoverData)
    if(hoverData == None):
        hoverData=''
        return 0,0,0,'State'
    else:
        s = df[df['State'] == hoverData['points'][0]['location']]
        return s.iloc[0]['Confirmed'], s.iloc[0]['Recovered'], s.iloc[0]["Death"],s.iloc[0]["State"]

@app.callback(Output('plot', 'figure'),
             [Input('opt', 'value')])
def update_figure(input1):
    # filtering the data
    if(input1 == None):
        input1='Telangana'
    date_values= df_india[df_india["State/UnionTerritory"]==input1].iloc[:,1]
    confirmed_values= df_india[df_india["State/UnionTerritory"]==input1].iloc[:,8]
    deaths_values=df_india[df_india["State/UnionTerritory"]==input1].iloc[:,7]
    recovered_values=df_india[df_india["State/UnionTerritory"]==input1].iloc[:,6]

    figline = go.Figure()
    figline.add_trace(go.Scatter(x=date_values, y=confirmed_values,
                    mode='lines+markers',name='confirmed cases',
                   ))
    figline.add_trace(go.Scatter(x=date_values, y=deaths_values,
                    mode='lines+markers',name='no. of deaths'
                    ))
    figline.add_trace(go.Scatter(x=date_values, y=recovered_values,
                    mode='lines+markers',name='recovered cases'))
    figline.update_yaxes(nticks=7,tickmode="auto") #Scaling Y-axis
    figline.update_xaxes(nticks=7,tickmode="auto") #Scaling Y-axis
    figline.update_layout(
    title="StateWise- COVID-19 Analysis",
    xaxis_title="Day",
    yaxis_title="No. of people"
    )
    return figline

if __name__ == '__main__':
    app.run_server(debug=True)