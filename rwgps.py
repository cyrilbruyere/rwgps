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

####################
###   HEATMAPS   ###
####################

# YTD, MTD
ytd = dt.date.today().year
mtd = dt.date.today().month

# 6 MONTH SEASONS' TARGETS
winter = pd.DataFrame([[10, 0, 0, 0, 10], [0, 30, 0, 0, 0], [0, 0, 20, 0, 0], [0, 0, 0, 30, 0], [0, 0, 0, 0, 0]],
                      index = ['GRAVEL', 'HT', 'ROAD', 'URBAN', 'VTT'],
                      columns = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
summer = pd.DataFrame([[30, 0, 0, 0, 0], [0, 0, 0, 0, 0], [20, 30, 70, 0, 0], [0, 0, 0, 20, 0], [0, 0, 0, 0, 0]],
                      index = ['GRAVEL', 'HT', 'ROAD', 'URBAN', 'VTT'],
                      columns = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])

unique_gears = ', '.join(trips['GEAR'].unique())
unique_names = ', '.join(trips['NAME'].unique())

# TARGET climbing for strength
everest = 8849 # valid for summer, eg E
montblanc = 4809 # valid for winter, eg H

# TARGE YTD, MTD
target_ytd = min(3, mtd) * 1/6 * winter + max(0, mtd - 9) * 1/6 * winter + max(0, mtd - 3) * 1/6 * summer - max(0, mtd - 9) * 1/6 * summer
target_mtd = 1/6 * winter
target_climb = 'Mont Blanc'
target_elevation = montblanc
if mtd in [4, 5, 6, 7, 8, 9]:
    target_mtd = 1/6 * summer
    target_climb = 'Everest'
    target_elevation = everest

# RIDES YTD, MTD
rides_ytd = trips[trips['YYYY'] == ytd].copy()
rides_mtd = trips[(trips['YYYY'] == ytd) & (trips['MM'] == mtd)].copy()

# AVERAGE REST
day_of_year = dt.date.today().timetuple().tm_yday
day_of_month = dt.date.today().day

rest_ytd = round(day_of_year / rides_ytd['DATE'].nunique(), 1)
rest_mtd = round(day_of_month / rides_mtd['DATE'].nunique(), 1)

# YEARLY STATS
velotaf_stats = trips[trips['NAME'] == 'Velotaf'][['YYYY', 'DATE', 'DISTANCE']]
velotaf_stats = velotaf_stats.groupby(['YYYY']).agg({'DATE' : 'nunique', 'DISTANCE' : 'sum'}).reset_index().T
velotaf_stats = velotaf_stats.astype(int)
velotaf_stats.columns = velotaf_stats.iloc[0, :]
velotaf_stats.index = ['An', 'Jours', 'Kms']
velotaf_stats = velotaf_stats.iloc[1:, :]
velotaf_stats = velotaf_stats.reset_index()

rides_stats = trips[trips['GEAR'].isin(['ROAD', 'GRAVEL'])][['YYYY', 'DATE', 'DISTANCE', 'DUREE']]
rides_stats = rides_stats.groupby(['YYYY']).agg({'DATE' : 'nunique', 'DISTANCE' : ['sum', 'mean'], 'DUREE' : 'sum'}).reset_index()
rides_stats.columns = ['YYYY', 'DATE', 'DISTANCE', 'KM MOY', 'DUREE']
rides_stats['SPEED'] = round(rides_stats['DISTANCE'] / rides_stats['DUREE'], 1)
rides_stats = rides_stats.fillna(0)
rides_stats = rides_stats.drop(['DUREE'], axis = 1)
rides_stats.columns = ['YYYY', 'DATE', 'DISTANCE', 'KM MOY', 'SPEED']
rides_stats[['YYYY', 'DATE', 'DISTANCE']] = rides_stats[['YYYY', 'DATE', 'DISTANCE']].astype(int)
rides_stats[['KM MOY', 'SPEED']] = round(rides_stats[['KM MOY', 'SPEED']], 1)
rides_stats = rides_stats.T
rides_stats.columns = rides_stats.iloc[0, :]
rides_stats.index = ['An', 'Jours', 'Km', 'AvgKm', 'Km/h']
rides_stats = rides_stats.iloc[1:, :]
rides_stats = rides_stats.reset_index()

total_stats = trips[['YYYY', 'DATE', 'DUREE']]
total_stats = total_stats.groupby(['YYYY']).agg({'DATE' : 'nunique', 'DUREE' : 'sum'}).reset_index().T
total_stats = total_stats.astype(int)
total_stats.columns = total_stats.iloc[0, :]
total_stats.index = ['An', 'Jours', 'Heures']
total_stats = total_stats.iloc[1:, :]
total_stats = total_stats.reset_index()

semester_stats = trips[['YYYY', 'MM', 'DATE', 'DUREE']]
semester_stats = semester_stats.groupby(['YYYY', 'MM']).agg({'DATE' : 'nunique', 'DUREE' : 'sum'}).reset_index()
semester_rides = trips[trips['GEAR'].isin(['ROAD', 'GRAVEL'])][['YYYY', 'MM', 'DISTANCE', 'ELEVATION']]
semester_rides = semester_rides.groupby(['YYYY', 'MM']).agg({'DISTANCE' : ['mean', 'sum', 'ELEVATION' : 'sum']}).reset_index()
semester_rides.columns = ['YYYY', 'MM', 'KM_AVG', 'DISTANCE', 'ELEVATION']
semester_rides['RATIO'] = round(semester_rides['ELEVATION'] / semester_rides['DISTANCE'], 1)
semester_rides = semester_rides.drop(['DISTANCE', 'ELEVATION'], axis = 1)
semester_stats = pd.merge(semester_stats, semester_rides, how = 'left', left_on = ['YYYY', 'MM'], right_on = ['YYYY', 'MM'])
semester_stats = semester_stats.fillna(0)
semester_stats['YYYY-MM'] = semester_stats['YYYY'].astype(str) + '-' + semester_stats['MM'].astype(str)
semester_stats = semester_stats.drop(['YYYY', 'MM'], axis = 1)
semester_stats = semester_stats[['YYYY-MM', 'DUREE', 'KM_AVG', 'RATIO']]
semester_stats[['DUREE']] = semester_stats[['DUREE']].astype(int)
semester_stats[['KM_AVG', 'RATIO']] = round(semester_stats[['KM_AVG', 'RATIO']], 1)
semester_stats = semester_stats.T
semester_stats.columns = semester_stats.iloc[0, :]
semester_stats.index = ['An', 'Heures', 'AvgKm', 'Ratio']
semester_stats = semester_stats.iloc[1:, :]
semester_stats = semester_stats.reset_index()

# SUMMARY YTD
rides_ytd = rides_ytd[['GEAR', 'NAME', 'DUREE']]
days_ytd = int(rides_ytd['DUREE'].sum() // 24)
hours_ytd = int(rides_ytd['DUREE'].sum() % 24)
empty = pd.DataFrame({'GEAR' : ['GRAVEL', 'HT', 'ROAD', 'URBAN', 'VTT'],
                       'NAME' : ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'],
                       'DUREE' : [0, 0, 0, 0, 0]})
rides_ytd = pd.concat([rides_ytd, empty], axis = 0)
rides_ytd = rides_ytd.groupby(['GEAR', 'NAME']).sum()
rides_ytd = rides_ytd.unstack('NAME')
rides_ytd = rides_ytd.droplevel(0, axis = 1)
rides_ytd = rides_ytd.rename_axis(index=None, columns=None)
rides_ytd = rides_ytd[['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch']]

# SUMMARY MTD
rides_mtd = rides_mtd[['GEAR', 'NAME', 'DUREE']]
days_mtd = int(rides_mtd['DUREE'].sum() // 24)
hours_mtd = int(rides_mtd['DUREE'].sum() % 24)
climb_mtd = int(trips[(trips['YYYY'] == ytd) & (trips['MM'] == mtd)]['ELEVATION'].sum() - target_elevation)
empty = pd.DataFrame({'GEAR' : ['GRAVEL', 'HT', 'ROAD', 'URBAN', 'VTT'],
                       'NAME' : ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'],
                       'DUREE' : [0, 0, 0, 0, 0]})
rides_mtd = pd.concat([rides_mtd, empty], axis = 0)
rides_mtd = rides_mtd.groupby(['GEAR', 'NAME']).sum()
rides_mtd = rides_mtd.unstack('NAME')
rides_mtd = rides_mtd.droplevel(0, axis = 1)
rides_mtd = rides_mtd.rename_axis(index=None, columns=None)
rides_mtd = rides_mtd[['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch']]

# STATUS YTD, MTD
status_ytd = rides_ytd.fillna(0) - target_ytd
status_mtd = rides_mtd.fillna(0) - target_mtd

total_ytd = status_ytd.copy()
total_mtd = status_mtd.copy()

status_ytd = status_ytd.replace(0, np.nan)
status_mtd = status_mtd.replace(0, np.nan)

ytd_sum = status_ytd.sum(axis = 0).to_list()
status_ytd.loc['SUM'] = ytd_sum

mtd_sum = status_mtd.sum(axis = 0).to_list()
status_mtd.loc['SUM'] = mtd_sum

total_ytd = round(total_ytd.values.sum(), 1)
total_mtd = round(total_mtd.values.sum(), 1)

# HEATMAPS YTD, MTD
fig_ytd = px.imshow(status_ytd.values,
                    x = status_ytd.columns,
                    y = status_ytd.index,
                    text_auto = '.0f',
                    color_continuous_scale = ['red', 'white', 'green'],
                    color_continuous_midpoint = 0,
                    aspect = 'auto')

fig_ytd.update_layout(coloraxis_showscale = False, font = dict(size = 18), plot_bgcolor = 'white')
fig_ytd.update_xaxes(side = 'top')
fig_ytd.update_traces(textfont_size = 28)

fig_ytd.write_image('ytd.png')

fig_mtd = px.imshow(status_mtd.values,
                    x = status_mtd.columns,
                    y = status_mtd.index,
                    text_auto = '.1f',
                    color_continuous_scale = ['red', 'white', 'green'],
                    color_continuous_midpoint = 0,
                    aspect = 'auto')

fig_mtd.update_layout(coloraxis_showscale = False, font = dict(size = 18), plot_bgcolor = 'white')
fig_mtd.update_xaxes(side = 'top')
fig_mtd.update_traces(textfont_size = 28)

fig_mtd.write_image('mtd.png')

###############
###   PMC   ###
###############

df = trips[['DATE', 'DUREE', 'DISTANCE', 'ELEVATION', 'GEAR']].copy()
df = df.sort_values(['DATE'])

df.loc[(df['GEAR'] == 'HT') & (df['DUREE'] == 0), 'DUREE'] = 0.75
df.loc[(df['GEAR'] == 'HT') & (df['DISTANCE'] == 0), 'DISTANCE'] = 21
df.loc[(df['GEAR'] == 'HT') & (df['ELEVATION'] == 0), 'ELEVATION'] = 200

df = df.drop(['GEAR'], axis = 1)
df = df.groupby(['DATE']).sum().reset_index()

df['SPEED'] = df['DISTANCE'] / df['DUREE']
df['RATIO'] = df['ELEVATION'] / df['DISTANCE']
df['IF'] = df['SPEED'] / 27.5 * np.power(df['RATIO'], 1/3) / math.pow(22.5, 1/3)
df['TSS'] = df['DUREE'] * np.power(df ['IF'], 2) * 100
df['DATE'] = df['DATE'].astype(str)

# Toutes les dates doivent être prises en compte
sdate = dt.date(2014, 1, 1)   # start date
edate = dt.date.today()   # end date
pmc = pd.DataFrame(index = pd.date_range(sdate,edate-dt.timedelta(days=1),freq='d'))
pmc = pmc.reset_index()
pmc.columns = ['DATE']

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

print(pmc[['DATE', 'TSS', 'ATL', 'CTL', 'TSB+', 'TSB-']].head(20))

rolling_3m = edate - relativedelta(months = 3)
rolling_3m = str(rolling_3m.year) + '-' + str(rolling_3m.month).zfill(2) + '-' + str(rolling_3m.day).zfill(2)
pmc = pmc[pmc['DATE'] > rolling_3m]

# Création du graphique
graf = go.Figure()
graf.update_layout(title = 'PMC')
graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['CTL'].values, mode = 'lines', name = 'CTL'))
graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['TSB-'].values, mode = 'lines', fill='tozeroy', name = 'TSB-'))
graf.add_trace(go.Scatter(x = pmc['DATE'], y = pmc['TSB+'].values, mode = 'lines', fill='tozeroy', name = 'TSB+'))

graf.write_image('pmc.png')

# Images à envoyer
with open('pmc.png', 'rb') as file:
    msgImage_pmc = MIMEImage(file.read())
    msgImage_pmc.add_header('Content-ID', '<pmc>')

# ENVOI DE L'EMAIL

# Images à envoyer
with open('ytd.png', 'rb') as file_ytd:
    msgImage_ytd = MIMEImage(file_ytd.read())
    msgImage_ytd.add_header('Content-ID', '<ytd>')

with open('mtd.png', 'rb') as file_mtd:
    msgImage_mtd = MIMEImage(file_mtd.read())
    msgImage_mtd.add_header('Content-ID', '<mtd>')

# Texte à envoyer
# msgtext = MIMEText('<br> <img src="cid:ytd"> </br>', 'html')
msg = """
Bonjour,<br><br>
Ride status du mois : <strong>{} h</strong><br>
{} climb du mois : <strong>{} m</strong><br>
Repos moyen du mois : <strong>{} j</strong><br>
<img src='cid:mtd'><br>
<br>
Ride status de l'année : <strong>{} h</strong><br>
Repos moyen de l'année : <strong>{} j</strong><br>
<img src='cid:ytd'><br>
<br>
Stats des 6 derniers mois : <strong>{}</strong><br>
<img src='cid:pmc'><br>
<br>
Moving time du le mois : <strong>{} j {} h</strong><br>
Moving time de l'année : <strong>{} j {} h</strong><br><br>
gears : {}<br>
names : {}<br>
<br>
Stats Velotaf : <strong>{}</strong><br>
Stats Rides : <strong>{}</strong><br>
Stats globales : <strong>{}</strong><br>
""".format(total_mtd, target_climb, climb_mtd, rest_mtd, total_ytd, rest_ytd, build_table(semester_stats, 'blue_light', font_size='12px'), days_mtd, hours_mtd, days_ytd, hours_ytd, unique_gears, unique_names, build_table(velotaf_stats, 'blue_light', font_size='12px'), build_table(rides_stats, 'blue_light', font_size='12px'), build_table(total_stats, 'blue_light', font_size='12px'))

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

