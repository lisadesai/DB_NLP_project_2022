from dash import Dash, dcc, html, Input, Output, ctx
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud, STOPWORDS
from datetime import date

app = Dash(__name__)

def post(ttlVal,txtVal):
    day  = date.today()
    today = day.strftime("%Y-%m-%d")
    print(today)
    bank = "User"
    title = ttlVal
    code = requests.post("http://db-us-intern-3.appspot.com/api/text?title="+title+"&timestamp="+today+"&bank="+bank+"&text="+txtVal)
    print(code)
    if code == "<Response [200]>":
        return "Post Successful"
    else:
        return "Post Unsuccessful"
def get():
    val = json.loads(requests.get("http://db-us-intern-3.appspot.com/api/text").text)
    return json.dumps(val, indent=4)
def delete(ttlVal):
    code = requests.delete("http://db-us-intern-3.appspot.com/api/text?text="+ttlVal)
    if code == "<Response [200]>":
        return "Successful delete"
    else:
        return "Unsuccessful delete"

def get_options():
    list_analysis = ['Sentiment Over Time','Article Count by Month','Top 10 Content Categories','German vs English Sentiment','Competitor Sentiment','Salience By Entities','Articles by Month']
    dict_list = []
    for i in list_analysis:
        dict_list.append({'label': i, 'value': i})
    return dict_list

url = "http://db-us-intern-3.appspot.com/api/text"
articleList = json.loads(requests.get(url).text)
dateList = []#['11-05-2022','11-05-2022','11-06-2022','11-05-2022','11-06-2022','11-06-2022']
sentimentList = []#[100,120,130,90,70,80]
bankList = []#['DB','BNP','DB','Citi','Citi','BNP']
sentList = []
dbenpos = 0
dbdepos = 0
dbenneu = 0
dbdeneu = 0
dbenneg = 0
dbdeneg = 0
citipos = 0
citineu = 0
citineg = 0
bnppos = 0
bnpneu = 0
bnpneg = 0

for article in articleList:
    for component in articleList[article]:
        if component == "timestamp":
            dateList.append(articleList[article][component])
        if component == "magnitude":
            sentimentList.append(float(articleList[article][component]))
        if component == "bank":
            bankList.append(articleList[article][component])
        if component == "sentiment":
            sentList.append(articleList[article][component])
        #print (component + ":" + articleList[article][component])
for i in range(len(sentList)):
    if bankList[i] == 'dben':
        if sentList[i] == 'positive':
            dbenpos +=1
        if sentList[i] == 'neutral':
            dbenneu +=1
        if sentList[i] == 'negative':
            dbenneg +=1    
    if bankList[i] == 'dbde':
        if sentList[i] == 'positive':
            dbdepos +=1
        if sentList[i] == 'neutral':
            dbdeneu +=1
        if sentList[i] == 'negative':
            dbdeneg +=1
    if bankList[i] == 'citi':
        if sentList[i] == 'positive':
            citipos +=1
        if sentList[i] == 'neutral':
            citineu +=1
        if sentList[i] == 'negative':
            citineg +=1  
    if bankList[i] == 'bnp':
        if sentList[i] == 'positive':
            bnppos +=1
        if sentList[i] == 'neutral':
            bnpneu +=1
        if sentList[i] == 'negative':
            bnpneg +=1  
print(len(dateList))
print(len(sentimentList))
print(len(bankList))
print(dateList)
print(sentimentList)
print(bankList)

z = zip(dateList,sentimentList,bankList)
zs = sorted(z)
u = zip(*zs)
map(list, u)
dates, sentiments, bankss = map(list, u)
count = []
bnpcount = 0
decount = 0
encount = 0
citicount = 0
for i in range(len(bankss)):
    if bankss[i] == 'dben':
        encount += 1
        count.append(encount)
    elif bankss[i] == 'dbde':
        decount += 1
        count.append(decount)
    elif bankss[i] == 'citi':
        citicount += 1
        count.append(citicount)
    elif bankss[i] == 'bnp':
        bnpcount += 1
        count.append(bnpcount)
lastbnp = 0
lastde = 0
lasten = 0
lastciti = 0
for i in range(len(sentimentList)):
    if bankss[i] == 'dben':
        sentiments[i] = lasten + sentiments[i]
        lasten = sentiments[i]
    elif bankss[i] == 'dbde':
        sentiments[i] = lastde + sentiments[i]
        lastde = sentiments[i]
    elif bankss[i] == 'citi':
        sentiments[i] = lastciti + sentiments[i]
        lastciti = sentiments[i]
    elif bankss[i] == 'bnp':
        sentiments[i] = lastbnp + sentiments[i]
        lastbnp = sentiments[i]
#fig = px.line(df,x='Date',y='Sentiment',color='Bank')


url = "https://db-us-intern-3.appspot.com/api/please"
banks = ["dben", "citi", "bnp", "dbde"]

DBEN_DATA = {}
DBDE_DATA = {}
BNP_DATA = {}
CITI_DATA = {}

for bank in banks:
    msg = "?bank=" + bank

    # use requests library to send HTTP requests
    # in this example, GET sentiment analysis data
    data = json.loads(requests.get(url+msg).text)
    if bank == "dben":
        DBEN_DATA = data
    elif bank == "dbde":
        DBDE_DATA = data
    elif bank == "citi":
        CITI_DATA = data
    elif bank == "bnp":
        BNP_DATA = data
    banks = [DBEN_DATA, BNP_DATA, CITI_DATA]
    langs = [DBEN_DATA, DBDE_DATA] 
    def find_values(id, json_repr):
        results = []

        def _decode_dict(a_dict):
            try:
                results.append(a_dict[id])
            except KeyError:
               pass
            return a_dict

        json.loads(json_repr, object_hook=_decode_dict) # Return value ignored.
        return results

entity_type_salience_per_bank = []
entity_type_salience = {}

entity_name_bank = {}

# https://stackoverflow.com/questions/41825868/update-python-dictionary-add-another-value-to-existing-key
def set_key(dictionary, key, value):
    if key not in dictionary:
        dictionary[key] = value
    elif type(dictionary[key]) == list:
        dictionary[key].append(value)
    else:
        dictionary[key] = [dictionary[key], value]

# loop through analyses and look at entity analysis
for bank in banks:
    for key in bank:
        entry = bank.get(key)
        
        bnk = entry.get('bank')
        # extract entity analysis
        entities = find_values('entity analysis', json.dumps(entry))
        entities = entities[0]

        # get entity type and entity salience
        for entity_key, entity in entities.items():
            entity_type = entity.get('entity type')
            entity_salience = entity.get('entity salience')
            set_key(entity_type_salience, entity_type, entity_salience)
            entity_nm = entity.get('entity name')
            set_key(entity_name_bank, bnk, entity_nm)

    # find average
    for entity_type, entity_salience in entity_type_salience.items():
        if type(entity_salience) == list:
            entity_salience = [float(x) for x in entity_salience]
            sal = np.average(entity_salience)
        entity_type_salience[entity_type] = sal

    #print(entity_type_salience)
    entity_type_salience_per_bank.append(entity_type_salience)
    entity_type_salience = {}

entity_type_salience_per_bank_dict = {'db': pd.Series(entity_type_salience_per_bank[0]), 'citi': pd.Series(entity_type_salience_per_bank[1]), \
                                    'bnp': pd.Series(entity_type_salience_per_bank[2])}
print(entity_type_salience_per_bank)
entities_df = pd.DataFrame(entity_type_salience_per_bank, index = ['db', 'citi', 'bnp'])
entities_df = entities_df.T
entities_df = entities_df.sort_values(by=['db'], ascending=False)
entity_type_salience_fig = px.bar(entities_df, color_discrete_sequence=["blue", "red", "green"])#, x='Entity Type', y='Average Entity Salience')
entity_type_salience_fig.update_layout(title="Entity Type vs Salience",
                           legend_title="Bank", xaxis_title="Entity Type",
                           yaxis_title='Average Entity Salience')



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
                                      value='Sentiment Over Time', )
                              ],
                              style={'color': '#1E1E1E'})
                 ]),  # Define the left element
                 html.Div(className='eight columns div-for-charts bg-grey', children=[html.Div(dcc.Graph(id='graph'))]),
                 html.Div(children=[
                    dcc.Textarea(id = 'ttl',value ="Title",style={'width': '50%', 'height': 30}),
                    html.Button('Delete',id='Delete',n_clicks=0),
                    dcc.Textarea(id = 'txt',value ="Text",style={'width': '50%', 'height': 300}),
                    html.Br(),
                    html.Button('Post',id='Post',n_clicks=0),
                    html.Br(),
                    html.Br(),
                    html.Button('Get',id='Get',n_clicks=0),
                    html.Div(id = "Get Requests")
                    ])
                 
                 # Define the right element
             ])
])

@app.callback(
    Output('Get Requests','children'),
    Input('Post', 'n_clicks'),
    Input('Get', 'n_clicks'),
    Input('Delete', 'n_clicks'),
    Input('ttl','value'),
    Input('txt','value')
)
def displayClick(btn1,btn2,btn3,ttlVal,txtVal):
    msg = ""
    if "Post" == ctx.triggered_id:
        msg = post(ttlVal,txtVal)
    elif "Get" == ctx.triggered_id:
        msg = get()
    elif "Delete" == ctx.triggered_id:
        msg = delete(ttlVal,txtVal)
    return html.Div(msg)

@app.callback(
    Output('graph', 'figure'),
    Input(component_id='dropdown', component_property='value')
)
def select_graph(value):
    if value == 'Sentiment Over Time':
        print(len(dates))
        print(len(sentiments))
        print(len(banks))
        df = pd.DataFrame({
            'Date':dates,
            'Sentiment':sentiments,
            'Bank':bankss
        })
        fig = px.line(df,x='Date',y='Sentiment',color='Bank')
        fig.update_xaxes(title='Date').update_yaxes(title='Sentiment')
        return fig
    if value == 'Article Count by Month':
        df = pd.DataFrame({
            'Date':dates,
            'Count':count,
            'Bank':bankss
        })
        fig = px.line(df,x='Date',y='Count',color='Bank')
        fig.update_xaxes(title='Date').update_yaxes(title='Sentiment')
        return fig
    if value == 'Top 10 Content Categories':
        df = pd.DataFrame({
            'Article':['Business & Industrial','Finance','Business Finance','Banking','Utilities','Investing','Technology','Electronics','Society', 'Electricity'],
            'Count':[28,26,11,11,4,3,3,2,1,1]
        })
        fig = px.bar(df, x='Article',y='Count')
        fig.update_xaxes(title='Category')
        return fig
    if value == 'German vs English Sentiment':
        df = pd.DataFrame({
            'Sentiment':["Positive","Positive","Neutral","Neutral","Negative","Negative"],
            'Count':[dbdepos,dbenpos,dbdeneu,dbenneu,dbdeneg,dbenneg],
            'Language':['German','English','German','English','German','English']
        })
        fig = px.bar(df, x='Sentiment',y='Count',color="Language",barmode="group")
        return fig
    if value == 'Competitor Sentiment':
        df = pd.DataFrame({
            'Sentiment':["Positive","Positive","Positive","Neutral","Neutral","Neutral","Negative","Negative","Negative"],
            'Count':[dbenpos,citipos,bnppos,dbenneu,citineu,bnpneu,dbenneg,citineg,bnpneg],
            'Bank':['DB','Citi','BNP','DB','Citi','BNP','DB','Citi','BNP']
        })
        fig = px.bar(df, x='Sentiment',y='Count',color="Bank",barmode="group")
        return fig
    if value == 'Salience By Entities':
        return entity_type_salience_fig
    if value == 'Articles by Month':
        df = pd.DataFrame({
            'Article':['December','January','February','March','April','May','June','July','December','January','February','March','April','May','June','July','December','January','February','March','April','May','June','July'],
            'Count':[1,4,1,2,0,6,2,1,4,2,1,1,1,2,0,2,1,0,3,1,0,4,0,2],
            'Bank':['DB','DB','DB','DB','DB', 'DB', 'DB', 'DB', 'Citi','Citi', 'Citi','Citi','Citi','Citi','Citi','Citi','BNP','BNP','BNP','BNP','BNP','BNP','BNP','BNP'] 
        })
        fig = px.bar(df, x='Article',y='Count',color='Bank', barmode = 'group')
        return fig

if __name__ == '__main__':
    app.run_server(debug=True)