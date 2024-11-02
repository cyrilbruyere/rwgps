# API access
import requests
# DATA transform
import numpy as np
import pandas as pd
# # Graphics
import plotly.express as px
import plotly.graph_objects as go
from pretty_html_table import build_table
# Built in
import datetime as dt
from dateutil.relativedelta import relativedelta
import math
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

###################
###   SETTING   ###
###################

api_key = os.environ.get('api_key')
api_token = os.environ.get('api_token')

# NB : le token est régulièrement annulé. Pour le générer : https://r...gps.com/api
params = {"apikey": api_key,
          "version": "2",
          "auth_token": api_token
          }

url_user = os.environ.get('url_user')
url_trips = os.environ.get('url_trips')

#################
###   GEARS   ###
#################

response = requests.get(url_user, params = params, verify = False)
data = response.json()
# print(json.dumps(data, indent=4))

gears = []
user = data['user']
for v in user['gear']:
    gear=[]
    gear.append(v['id'])
    gear.append(v['nickname'])
    gears.append(gear)

gears = pd.DataFrame(gears, columns = ['ID_GEAR', 'GEAR'])

#################
###   TRIPS   ###
#################

response = requests.get(url_trips, params = params, verify = False)
data = response.json()
# print(json.dumps(data, indent=4))

records = data['results_count']

trips = []
i = 0
j = 0
for v in data['results']:
    # print(json.dumps(v, indent=4))
    i += 1
    trip = []
    trip.append(v['id'])
    trip.append(v['departed_at'])
    trip.append(v['moving_time']/3600)
    trip.append(v['distance']/1000)
    trip.append(v['elevation_gain'])
    trip.append(v['avg_hr'])
    trip.append(v['avg_cad'])
    trip.append(v['avg_speed'])
    trip.append(v['avg_watts'])
    trip.append(v['calories'])
    trip.append(v['name'])
    trip.append(v['gear_id'])
    trips.append(trip)

trips = pd.DataFrame(trips, columns = ['ID', 'DATE', 'DUREE', 'DISTANCE', 'ELEVATION', 'HR', 'CADENCE', 'SPEED', 'WATTS', 'CALORIES', 'NAME', 'ID_GEAR'])
trips = pd.merge(trips, gears, how = 'left', left_on = 'ID_GEAR', right_on = 'ID_GEAR')
trips = trips.drop(['ID_GEAR'], axis = 1)
trips['DATE'] = pd.to_datetime(trips['DATE'], yearfirst = True)
trips['YYYY'] = trips['DATE'].dt.year
trips['MM'] = trips['DATE'].dt.month
trips['DATE'] = trips['DATE'].dt.date
trips['SEASON'] = 'E'
trips.loc[trips['MM'].isin([1, 2, 3, 10, 11, 12]), 'SEASON'] = 'H'
trips.loc[trips['GEAR'] ==  'HT', 'ELEVATION'] = 0
trips['RATIO'] = trips['ELEVATION'] / trips['DISTANCE']
trips = trips[['DATE', 'NAME', 'GEAR', 'DISTANCE', 'ELEVATION', 'DUREE', 'SPEED', 'CADENCE', 'HR', 'WATTS', 'CALORIES', 'YYYY', 'MM', 'SEASON', 'RATIO']]

trips = trips[trips['NAME'] !=  'NOE']

# YTD, MTD
ytd = dt.date.today().year
mtd = dt.date.today().month

# RIDES YTD, MTD
rides_ytd = trips[trips['YYYY'] == ytd].copy()
rides_mtd = trips[(trips['YYYY'] == ytd) & (trips['MM'] == mtd)].copy()

###################
###   TARGETS   ###
###################

# 6 MONTH SEASONS' TARGETS
winter = pd.DataFrame({'TARGET' : [10, 30, 20, 30, 10, 100]},
                       index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch', 'Total'])
summer = pd.DataFrame({'TARGE' : [50, 30, 70, 20, 0, 170]},
                       index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch', 'Total'])

# TARGET climbing for strength
everest = 8849 # Asie
aconcagua = 6962 # Amérique
kilimandjaro = 5892 # Afrique
montblanc = 4809 # Europe

# TARGE YTD, MTD
target_ytd = min(3, mtd) * 1/6 * winter + max(0, mtd - 9) * 1/6 * winter + max(0, mtd - 3) * 1/6 * summer - max(0, mtd - 9) * 1/6 * summer
target_mtd = 1/6 * winter
if mtd in [4, 5, 6, 7, 8, 9]:
    target_mtd = 1/6 * summer

target_ytd = target_ytd.reset_index(names = ['NAME'])
target_mtd = target_mtd.reset_index(names = ['NAME'])

#################
###   STATS   ###
#################

# STATUS YTD
rides_ytd = rides_ytd[rides_ytd['NAME'].isin(['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])][['NAME', 'DUREE']]
empty = pd.DataFrame({'NAME' : ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'],
                      'DUREE' : [0, 0, 0, 0, 0]})
rides_ytd = pd.concat([rides_ytd, empty], axis = 0)
rides_ytd = rides_ytd.groupby(['NAME']).sum().reset_index().fillna(0)
total_ytd = pd.DataFrame({'NAME' : ['Total'],
                          'DUREE' : [rides_ytd['DUREE'].sum()]})
rides_ytd = pd.concat([rides_ytd, total_ytd], axis = 0)
rides_ytd = pd.merge(target_ytd, rides_ytd, how = 'left', left_on = 'NAME', right_on = 'NAME')
rides_ytd['STATUS'] = rides_ytd['DUREE'] - rides_ytd['TARGET']
status_ytd = rides_ytd[['NAME', 'STATUS']].copy().T
status_ytd.index = ['Quand', 'Status']
status_ytd = status_ytd.reset_index()
status_ytd.columns = status_ytd.iloc[0].to_list()
status_ytd = status_ytd.iloc[1:]

# STATUS MTD
rides_mtd = rides_mtd[rides_mtd['NAME'].isin(['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])][['NAME', 'DUREE']]
empty = pd.DataFrame({'NAME' : ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'],
                      'DUREE' : [0, 0, 0, 0, 0]})
rides_mtd = pd.concat([rides_mtd, empty], axis = 0)
rides_mtd = rides_mtd.groupby(['NAME']).sum().reset_index().fillna(0)
total_mtd = pd.DataFrame({'NAME' : ['Total'],
                          'DUREE' : [rides_mtd['DUREE'].sum()]})
rides_mtd = pd.concat([rides_mtd, total_mtd], axis = 0) 
rides_mtd = pd.merge(target_mtd, rides_mtd, how = 'left', left_on = 'NAME', right_on = 'NAME')
rides_mtd['STATUS'] = rides_mtd['DUREE'] - rides_mtd['TARGET']
status_mtd = rides_mtd[['NAME', 'STATUS']].copy().T
status_mtd.index = ['Quand', 'Status']
status_mtd = status_mtd.reset_index()
status_mtd.columns = status_mtd.iloc[0].to_list()
status_mtd = status_mtd.iloc[1:]

# PMC
df = trips[['DATE', 'DUREE', 'DISTANCE', 'ELEVATION', 'GEAR']].copy()
df = df.sort_values(['DATE'])

df.loc[(df['GEAR'] == 'HT') & (df['DUREE'] == 0), 'DUREE'] = 0.75
df.loc[(df['GEAR'] == 'HT') & (df['DISTANCE'] == 0), 'DISTANCE'] = 21
df.loc[(df['GEAR'] == 'HT') & (df['ELEVATION'] == 0), 'ELEVATION'] = 200

# Facteur de correction pour la vitesse GRAVEL, URBAN & MTB
df['COEF'] = 1
df.loc[df['GEAR'].isin(['URBAN', 'GRAVEL']), 'COEF'] = 1.10
df.loc[df['GEAR'].isin(['MTB']), 'COEF'] = 1.25
df['DISTANCE_PMC'] = df['DISTANCE'] * df['COEF']

df = df.drop(['GEAR', 'COEF'], axis = 1)
df = df.groupby(['DATE']).sum().reset_index()

df['SPEED'] = df['DISTANCE'] / df['DUREE']
df['SPEED_PMC'] = df['DISTANCE_PMC'] / df['DUREE']
df['RATIO'] = df['ELEVATION'] / df['DISTANCE']

df['IF'] = df['SPEED_PMC'] / 27.5 * np.power(df['RATIO'], 1/3) / math.pow(22.5, 1/3)
df['TSS'] = df['DUREE'] * np.power(df ['IF'], 2) * 100
df['DATE'] = df['DATE'].astype(str)

# Toutes les dates doivent être prises en compte
sdate = dt.date(2014, 1, 1)   # start date
edate = dt.date.today()   # end date
pmc = pd.DataFrame(index = pd.date_range(sdate,edate-dt.timedelta(days=1),freq='d'))
pmc = pmc.reset_index()
pmc.columns = ['DATE']

pmc['YYYY'] = pmc['DATE'].dt.year
pmc['MM'] = pmc['DATE'].dt.month
pmc['YYYY-MM'] = pmc['YYYY'].astype(str) + '-' + pmc['MM'].astype(str)
pmc['DATE'] = pmc['DATE'].dt.strftime('%Y-%m-%d')

pmc = pd.merge(pmc, df[['DATE', 'TSS']], how = 'left', left_on = 'DATE', right_on = 'DATE')
pmc = pmc.fillna(0)

pmc['ATL'] = 0
pmc['CTL'] = 0
pmc = pmc.sort_values(['DATE'])
pmc = pmc.reset_index()
for index, row in pmc.iterrows():
    if index != 0:
        pmc.at[index, 'ATL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/7)) + pmc.at[index - 1, 'ATL'] * math.exp(-1/7)
        pmc.at[index, 'CTL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/42)) + pmc.at[index - 1, 'CTL'] * math.exp(-1/42)
    else:
        pmc.at[index, 'ATL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/7))
        pmc.at[index, 'CTL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/42))

pmc['TSB+'] = pmc.apply(lambda x: max(x['CTL'] - x['ATL'], 0), axis = 1)
pmc['TSB-'] = pmc.apply(lambda x: min(x['CTL'] - x['ATL'], 0), axis = 1)

rolling_3m = (edate - relativedelta(months = 3)).replace(day = 1)
rolling_3m = str(rolling_3m.year) + '-' + str(rolling_3m.month).zfill(2) + '-' + str(rolling_3m.day).zfill(2)
pmc = pmc[pmc['DATE'] > rolling_3m]

# Création du graphique
graf = go.Figure()
# graf.update_layout(title = 'PMC')
graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['CTL'].values, mode = 'lines', name = 'CTL'))
graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['TSB-'].values, mode = 'lines', fill='tozeroy', name = 'TSB-'))
graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['TSB+'].values, mode = 'lines', fill='tozeroy', name = 'TSB+'))

graf.write_image('pmc.png')

# Images à envoyer
with open('pmc.png', 'rb') as file:
    msgImage_pmc = MIMEImage(file.read())
    msgImage_pmc.add_header('Content-ID', '<pmc>')

# Tendance
trend = pmc[['YYYY-MM', 'DATE', 'DUREE', 'CTL', 'TSB+', 'TSB-']].copy()
trend = trend.sort_values(['DATE'], ascending = True)
trend['TSB'] = trend['TSB+'] + trend['TSB-']
trend = trend[['YYYY-MM', 'DUREE', 'CTL', 'TSB', 'TSB-']]
trend['ON'] = 0
trend.loc[trend['DUREE'] > 0, 'ON'] = 1
trend = trend.groupby(['YYYY-MM']).agg({'DUREE' : ['sum', 'nunique'],
                                        'ON' : 'sum',
                                        'CTL' : ['first', 'mean'],
                                        'TSB' : 'mean',
                                        'TSB-' : 'min'}).reset_index()
trend.columns = ['YYYY-MM', 'DUREE', 'DAYS', 'ON', 'FstCTL', 'AvgCTL', 'AvgTSB', 'MinTSB']
trend['REST'] = trend['DAYS'] / trend['ON']
trend = trend.fillna(0)
firstclt = trend['FstCTL'].to_list()
lastclt = firstclt[1:]
lastclt.append(pmc['CTL'].iloc[-1])
trend['LstCTL'] = lastclt
trend['CTL'] = trend['LstCTL'] - trend['FstCTL']

trend = trend['YYYY-MM', 'DUREE', 'REST', 'CTL', 'AvgCTL', 'AvgTSB', 'MinTSB'].T
trend.index = ['YYYY-MM', 'Heures', 'Repos', 'gapCTL', 'avgCTL', 'avgTSB', 'minTSB']
trend = trend.reset_index()
trend.columns = trend.iloc[0].to_list()
trend = trend.iloc[1:]

#############
### EMAIL ###
#############

# msgtext = MIMEText('<br> <img src="cid:ytd"> </br>', 'html')
msg = """
Bonjour,<br><br>
<strong>Etat du mois en cours</strong> : {}<br>
<strong>Etat de l'année en cours</strong> : {}<br>
<strong>Tendance des derniers mois</strong> : {}<br>
<br>
<img src='cid:pmc'><br>

""".format(build_table(status_mtd, 'blue_light', font_size='12px'), build_table(status_ytd, 'blue_light', font_size='12px'), build_table(trend, 'blue_light', font_size='12px'))

msgtext = MIMEText(msg, 'html')

msg = MIMEMultipart()
msg['Subject'] = 'Ride status'
msg.attach(msgtext)
msg.attach(msgImage_ytd)
msg.attach(msgImage_mtd)
msg.attach(msgImage_pmc)

port = 465
smtp_server = 'smtp.gmail.com'
user_email = os.environ.get('user_email')
email_token = os.environ.get('email_token')

try:
    context = ssl.create_default_context() # ne fonctionne pas
    server = smtplib.SMTP_SSL(smtp_server, port, context = context)
    server.login(user_email, email_token)
    server.sendmail(user_email, user_email, msg.as_string())
except:
    print('Something went wrong...')

