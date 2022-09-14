import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import requests
import json

from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def get_options():
    list_analysis = ['Article Count', 'Sentiment Analysis', 'Keyword Analysis', 'Sentiment Frequency', 'Topics vs Time', 'German vs English', 'Salience Correlation']
    dict_list = []
    for i in list_analysis:
        dict_list.append({'label': i, 'value': i})

    return dict_list


# define endpoint url
url = "http://127.0.0.1:8080/api/text"

# use requests library to send HTTP requests
# in this example, GET sentiment analysis data
data = json.loads(requests.get(url).text)

# data cleanup
json_a = []
for key in data:
    json_a.append(data[key])
df = pd.DataFrame(json_a)
df['date'] = pd.to_datetime(df["timestamp"]).dt.date
app.layout = html.Div(children=[
    html.Div(className='row',  # Define the row element
             children=[
                 html.Div(className='four columns div-user-controls', children=[
                     html.H2('Dashly - News Article Analysis'),
                     html.P('''Choose a context from dropdown below to visualize'''),
                     html.Div(className='div-for-dropdown',
                              children=[
                                  dcc.Dropdown(
                                      id='dropdown',
                                      options=get_options(),
                                      multi=False,
                                      value='Article Count', )
                              ],
                              style={'color': '#1E1E1E'})
                 ]),  # Define the left element
                 html.Div(className='eight columns div-for-charts bg-grey', children=[html.Div(dcc.Graph(id='graph'))])
                 # Define the right element
             ])
])


@app.callback(
    Output('graph', 'figure'),
    [Input(component_id='dropdown', component_property='value')]
)
def select_graph(value):
    if value == 'Article Count':
        fig = px.line(df.groupby(['date'])['date'].count(), x='date', title='Article counts by date')
        fig.update_xaxes(title='Date').update_yaxes(title='Article Count')
        return fig
    elif value == 'Sentiment Analysis':
        fig = px.bar(df, x='date', y="sentiment", color="sentiment", title='Sentiment Analysis')
        fig.update_xaxes(title='Date').update_yaxes(title='Sentiment Count')
        return fig
    elif value == 'Keyword Analysis':
        fig = px.bar(df, x='date', y="text", color="text", title='Keyword Analysis')
        fig.update_xaxes(title='Date').update_yaxes(title='Keyword Count')
        return fig
    elif value == 'Sentiment Frequency':
        fig = px.bar(df.groupby(['sentiment'])['sentiment'].count(), x='sentiment', title='Sentiment Frequency')
        fig.update_xaxes(title='Sentiment Count').update_yaxes(title='Sentiment')
        return fig


if __name__ == '__main__':
    app.run_server(debug=True)