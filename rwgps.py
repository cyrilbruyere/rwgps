# API access
import requests
# DATA transform
import numpy as np
import pandas as pd
# Graphics
import matplotlib.pyplot as plt
# import plotly.express as px
# import plotly.graph_objects as go
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

# CURRENT REST
current_rest = (dt.date.today() - trips['DATE'].sort_values(ascending = True).iloc[-1]).days

###################
###   TARGETS   ###
###################

# 6 MONTH SEASONS' TARGETS
jan = pd.DataFrame({'COUNT' : [1, 4, 4, 8, 0],
                    'TIME' : [1, 3, 6, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
feb = pd.DataFrame({'COUNT' : [1, 4, 4, 8, 0],
                    'TIME' : [1, 3, 6, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
mar = pd.DataFrame({'COUNT' : [2, 4, 4, 8, 0],
                    'TIME' : [4, 3, 8, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
apr = pd.DataFrame({'COUNT' : [2, 4, 4, 8, 0],
                    'TIME' : [5, 4, 12, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
may = pd.DataFrame({'COUNT' : [5, 4, 4, 5, 0],
                    'TIME' : [15, 6, 12, 5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
jun = pd.DataFrame({'COUNT' : [2, 4, 4, 8, 0],
                    'TIME' : [7, 6, 12, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
jul = pd.DataFrame({'COUNT' : [6, 2, 4, 5, 0],
                    'TIME' : [15, 6, 10, 5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
aug = pd.DataFrame({'COUNT' : [4, 2, 4, 5, 0],
                    'TIME' : [12, 6, 10, 5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
sep = pd.DataFrame({'COUNT' : [2, 4, 4, 8, 0],
                    'TIME' : [6, 6, 10, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
oct = pd.DataFrame({'COUNT' : [2, 4, 4, 8, 0],
                    'TIME' : [5, 4, 10, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
nov = pd.DataFrame({'COUNT' : [1, 4, 4, 8, 0],
                    'TIME' : [1, 3, 8, 7.5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
dec = pd.DataFrame({'COUNT' : [1, 3, 4, 5, 0],
                    'TIME' : [1, 3, 6, 5, 0]},
                    index = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])

# TARGE YTD, MTD
months = [jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec]
target_mtd = months[mtd - 1]
for i in range(mtd):
    if i == 0:
        target_ytd = months[i]
    else:
        target_ytd = target_ytd + months[i]

for i in range(12):
    if i == 0:
        days = months[i]['COUNT']
        days.name = str(i + 1)
        hours = months[i]['TIME']
        hours.name = str(i + 1)
    else:
        temp = months[i]['COUNT']
        temp.name = str(i + 1)
        days = pd.concat([days, temp], axis = 1)
        temp = months[i]['TIME']
        temp.name = str(i + 1)
        hours = pd.concat([hours, temp], axis = 1)

days['Total'] = days.sum(axis = 1)
hours['Total'] = hours.sum(axis = 1)
days.loc['Total'] = days.sum()
hours.loc['Total'] = hours.sum()

# days.to_csv('./target_days.csv', sep = ';')
# hours.to_csv('./target_days.csv', sep = ';')
# exit()

target_ytd = target_ytd.reset_index()
target_ytd.columns = ['NAME', 'COUNT', 'TIME']
target_ytd = pd.concat([target_ytd, pd.DataFrame([['Total', target_ytd['COUNT'].sum(), target_ytd['TIME'].sum()]], columns = target_ytd.columns)], axis = 0)
target_mtd = target_mtd.reset_index()
target_mtd.columns = ['NAME', 'COUNT', 'TIME']
target_mtd = pd.concat([target_mtd, pd.DataFrame([['Total', target_mtd['COUNT'].sum(), target_mtd['TIME'].sum()]], columns = target_mtd.columns)], axis = 0)

#################
###   STATS   ###
#################

# STATUS YTD
rides_ytd = rides_ytd[rides_ytd['NAME'].isin(['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])][['NAME', 'DATE', 'DUREE']]
empty = pd.DataFrame({'NAME' : ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'],
                      'DATE' : [None, None, None, None, None],
                      'DUREE' : [None, None, None, None, None]})
rides_ytd = pd.concat([rides_ytd, empty], axis = 0)
rides_ytd = rides_ytd.groupby(['NAME']).agg({'DATE' : 'nunique', 'DUREE' : 'sum'}).reset_index().fillna(0)
total_ytd = pd.DataFrame({'NAME' : ['Total'],
                          'DATE' : [rides_ytd['DATE'].sum()],
                          'DUREE' : [rides_ytd['DUREE'].sum()]})
rides_ytd = pd.concat([rides_ytd, total_ytd], axis = 0)
rides_ytd = pd.merge(target_ytd, rides_ytd, how = 'left', left_on = 'NAME', right_on = 'NAME')
rides_ytd['JOURS'] = round(rides_ytd['DATE'] - rides_ytd['COUNT'], 1)
rides_ytd['HEURES'] = round(rides_ytd['DUREE'] - rides_ytd['TIME'], 1)
rides_ytd = rides_ytd.astype(str)
rides_ytd['JOURS'] = rides_ytd['JOURS'] + ' j'
rides_ytd['HEURES'] = rides_ytd['HEURES'] + ' h'
status_ytd = rides_ytd[['NAME', 'JOURS', 'HEURES']].copy().T
status_ytd.index = [ytd, 'Jours', 'Heures']
status_ytd = status_ytd.reset_index()
status_ytd.columns = status_ytd.iloc[0].to_list()
status_ytd = status_ytd.iloc[1:]
status_ytd = status_ytd[[ytd, 'Total', 'WE', 'OFF', 'Afterwork', 'Velotaf', 'Lunch']]

# STATUS MTD
rides_mtd = rides_mtd[rides_mtd['NAME'].isin(['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])][['NAME', 'DATE', 'DUREE']]
empty = pd.DataFrame({'NAME' : ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'],
                      'DATE' : [None, None, None, None, None],
                      'DUREE' : [None, None, None, None, None]})
rides_mtd = pd.concat([rides_mtd, empty], axis = 0)
rides_mtd = rides_mtd.groupby(['NAME']).agg({'DATE' : 'nunique', 'DUREE' : 'sum'}).reset_index().fillna(0)
total_mtd = pd.DataFrame({'NAME' : ['Total'],
                          'DATE' : [rides_mtd['DATE'].sum()],
                          'DUREE' : [rides_mtd['DUREE'].sum()]})
rides_mtd = pd.concat([rides_mtd, total_mtd], axis = 0)
rides_mtd = pd.merge(target_mtd, rides_mtd, how = 'left', left_on = 'NAME', right_on = 'NAME')
rides_mtd['JOURS'] = round(rides_mtd['DATE'] - rides_mtd['COUNT'], 1)
rides_mtd['HEURES'] = round(rides_mtd['DUREE'] - rides_mtd['TIME'], 1)
rides_mtd = rides_mtd.astype(str)
rides_mtd['JOURS'] = rides_mtd['JOURS'] + ' j'
rides_mtd['HEURES'] = rides_mtd['HEURES'] + ' h'
status_mtd = rides_mtd[['NAME', 'JOURS', 'HEURES']].copy().T
status_mtd.index = [mtd, 'Jours', 'Heures']
status_mtd = status_mtd.reset_index()
status_mtd.columns = status_mtd.iloc[0].to_list()
status_mtd = status_mtd.iloc[1:]
status_mtd = status_mtd[[mtd, 'Total', 'WE', 'OFF', 'Afterwork', 'Velotaf', 'Lunch']]

# PMC
df = trips[['DATE', 'DUREE', 'DISTANCE', 'ELEVATION', 'GEAR']].copy()
df = df.sort_values(['DATE'])

df.loc[(df['GEAR'] == 'HT') & (df['DUREE'] == 0), 'DUREE'] = 0.75
df.loc[(df['GEAR'] == 'HT') & (df['DISTANCE'] == 0), 'DISTANCE'] = 21
df.loc[(df['GEAR'] == 'HT') & (df['ELEVATION'] == 0), 'ELEVATION'] = 200

# Facteur de correction pour la vitesse GRAVEL, URBAN & MTB
df['COEF'] = 1.0
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
pmc = pd.DataFrame(index = pd.date_range(sdate,edate,freq='d'))
pmc = pmc.reset_index()
pmc.columns = ['DATE']

pmc['YYYY'] = pmc['DATE'].dt.year
pmc['MM'] = pmc['DATE'].dt.month
pmc['YYYY-MM'] = pmc['YYYY'].astype(str) + '-' + pmc['MM'].astype(str).str.zfill(2)
pmc['DATE'] = pmc['DATE'].dt.strftime('%Y-%m-%d')

pmc = pd.merge(pmc, df[['DATE', 'DUREE', 'ELEVATION', 'TSS']], how = 'left', left_on = 'DATE', right_on = 'DATE')
pmc = pmc.fillna(0)

pmc['ATL'] = 0.0
pmc['CTL'] = 0.0
pmc = pmc.sort_values(['DATE'])
# pmc = pmc.reset_index()
for index, row in pmc.iterrows():
    if index != 0:
        pmc.at[index, 'ATL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/7)) + pmc.at[index - 1, 'ATL'] * math.exp(-1/7)
        pmc.at[index, 'CTL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/42)) + pmc.at[index - 1, 'CTL'] * math.exp(-1/42)
    else:
        pmc.at[index, 'ATL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/7))
        pmc.at[index, 'CTL'] = pmc.at[index, 'TSS'] * (1 - math.exp(-1/42))

pmc['TSB+'] = pmc.apply(lambda x: max(x['CTL'] - x['ATL'], 0), axis = 1)
pmc['TSB-'] = pmc.apply(lambda x: min(x['CTL'] - x['ATL'], 0), axis = 1)

rolling_months = (edate - relativedelta(months = 4)).replace(day = 1)
rolling_months = str(rolling_months.year) + '-' + str(rolling_months.month).zfill(2) + '-' + str(rolling_months.day).zfill(2)
pmc = pmc[pmc['DATE'] > rolling_months]

# # Création du graphique
# graf = go.Figure()
# # graf.update_layout(title = 'PMC')
# graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['CTL'].values, mode = 'lines', name = 'CTL'))
# graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['TSB-'].values, mode = 'lines', fill='tozeroy', name = 'TSB-'))
# graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['TSB+'].values, mode = 'lines', fill='tozeroy', name = 'TSB+'))

# graf.write_image('pmc.png')

# Avec Matplotlib
plt.plot(pmc['DATE'].str[-5:].values, pmc['CTL'].values, color = 'b', linewidth = 2)
plt.fill_between(pmc['DATE'].str[-5:].values, pmc['TSB-'].values, color = 'r')
plt.fill_between(pmc['DATE'].str[-5:].values, pmc['TSB+'].values, color = 'g')
plt.xticks(rotation = 90)
plt.grid(axis = 'y')
plt.locator_params(axis='x', nbins = 7)
plt.savefig("pmc.png")

# Images à envoyer
with open('pmc.png', 'rb') as file:
    msgImage_pmc = MIMEImage(file.read())
    msgImage_pmc.add_header('Content-ID', '<pmc>')

#############
### EMAIL ###
#############

# msgtext = MIMEText('<br> <img src="cid:ytd"> </br>', 'html')
msg = """
<strong>Etat du mois en cours</strong> : {}<br>
<strong>Etat de l'année en cours</strong> : {}<br>
<img src='cid:pmc'><br>

""".format(build_table(status_mtd, 'blue_light', font_size = '12px', text_align = 'center', width = '60px'),
           build_table(status_ytd, 'blue_light', font_size = '12px', text_align = 'center', width = '60px'))

msgtext = MIMEText(msg, 'html')

msg = MIMEMultipart()
msg['Subject'] = 'Ride status'
msg.attach(msgtext)
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

