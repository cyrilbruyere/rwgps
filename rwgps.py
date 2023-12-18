# API access
import requests
# Cleaning
import numpy as np
import pandas as pd
# # Graphics
import plotly.express as px
# Built in
import datetime as dt
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

api_key = os.environ.get('api_key')
api_token = os.environ.get('api_token')

# NB : le token est régulièrement annulé. Pour le générer : https://r...gps.com/api
params = {"apikey": api_key,
          "version": "2",
          "auth_token": api_token
          }

url_user = os.environ.get('url_user')
url_trips = os.environ.get('url_trips')

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

# 6 MONTH SEASONS' TARGETS
winter = pd.DataFrame([[10, 0, 0, 0, 10], [0, 30, 0, 0, 0], [0, 0, 20, 0, 0], [0, 0, 0, 30, 0], [0, 0, 0, 0, 0]],
                      index = ['GRAVEL', 'HT', 'ROAD', 'URBAN', 'VTT'],
                      columns = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])
summer = pd.DataFrame([[30, 0, 0, 0, 0], [0, 0, 0, 0, 0], [20, 30, 70, 0, 0], [0, 0, 0, 20, 0], [0, 0, 0, 0, 0]],
                      index = ['GRAVEL', 'HT', 'ROAD', 'URBAN', 'VTT'],
                      columns = ['OFF', 'Afterwork', 'WE', 'Velotaf', 'Lunch'])

unique_gears = trips['GEAR'].unique()
unique_names = trips['NAME'].unique()

# TARGE YTD, MTD
target_ytd = min(3, mtd) * 1/6 * winter + max(0, mtd - 9) * 1/6 * winter + max(0, mtd - 3) * 1/6 * summer - max(0, mtd - 9) * 1/6 * summer
target_mtd = 1/6 * winter
if mtd in [4, 5, 6, 7, 8, 9]:
    target_mtd = 1/6 * summer

# RIDES YTD, MTD
rides_ytd = trips[trips['YYYY'] == ytd]
rides_mtd = trips[(trips['YYYY'] == ytd) & (trips['MM'] == mtd)]

# SUMMARY YTD
rides_ytd = rides_ytd[['GEAR', 'NAME', 'DUREE']]
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
Ride status pour le mois en cours : <strong>{} h</strong><br><br>
<img src='cid:mtd'><br>
<br>
Ride status pour l'année en cours : <strong>{} h</strong><br><br>
<img src='cid:ytd'><br><br>
gears :<br>{}<br>
names :<br>{}<br>
<br>
""".format(total_mtd, total_ytd, unique_gears, unique_names)

msgtext = MIMEText(msg, 'html')

msg = MIMEMultipart()
msg['Subject'] = 'Ride status'
msg.attach(msgtext)
msg.attach(msgImage_ytd)
msg.attach(msgImage_mtd)

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

