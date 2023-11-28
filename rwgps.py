import requests, json
from pathlib import Path
import pandas as pd
import datetime as dt
# Graphics
import seaborn as sns
import matplotlib.pyplot as plt
# Email
# import win32com.client as win32
# from pretty_html_table import build_table
import smtplib, ssl

# RIDE DATA FROM RIDEWITHGPS.COM

user_id
apikey
token
url_user
url_trips
user_email

# NB : le token est régulièrement annulé. Pour le générer : https://r...gps.com/api
params = {"apikey": apikey,
          "version": "2",
          "auth_token": token
          }

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

# trips.to_csv('./data/rwgps/trips.csv', sep = ';', index = False)

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
rides_ytd = rides_ytd.fillna(0)

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
rides_mtd = rides_mtd.fillna(0)

# STATUS YTD, MTD
status_ytd = rides_ytd - target_ytd
status_mtd = rides_mtd - target_mtd

total_ytd = round(status_ytd.values.sum(), 1)
total_mtd = round(status_mtd.values.sum(), 1)

# HEATMAPS YTD, MTD
chemin_ytd = Path.cwd() / 'data' / 'ytd.png'
chemin_mtd = Path.cwd() / 'data' / 'mtd.png'

chemin_ytd = str(chemin_ytd).replace('\\', '/')
chemin_mtd = str(chemin_mtd).replace('\\', '/')

graph_path = [chemin_ytd, chemin_mtd]

ax1 = sns.heatmap(status_ytd,
            annot = True,
            fmt='.1f',
            cmap = 'RdBu',
            center = 0,
            cbar = False,
            square = True)
# ax1.tick_params(axis='x', colors='white')
# ax1.tick_params(axis='y', colors='white')
plt.savefig(graph_path[0])
plt.close()

ax2 = sns.heatmap(status_mtd,
            annot = True,
            fmt='.1f',
            cmap = 'RdBu',
            center = 0,
            cbar = False,
            square = True)
# ax2.tick_params(axis='x', colors='white')
# ax2.tick_params(axis='y', colors='white')
plt.savefig(graph_path[1])

# ENVOI DE L'EMAIL
outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
mail.To = user_email
mail.Subject = 'Ride Status'
attachment_0 = mail.Attachments.Add(graph_path[0])
attachment_0.PropertyAccessor.SetProperty('http://schemas.microsoft.com/mapi/proptag/0x3712001F', 'MyId0')
attachment_1 = mail.Attachments.Add(graph_path[1])
attachment_1.PropertyAccessor.SetProperty('http://schemas.microsoft.com/mapi/proptag/0x3712001F', 'MyId1')
mail.HTMLBody = """
    Bonjour,<br><br>
    Ride status pour le mois en cours : <strong>{} h</strong><br><br>
    <img src='cid:MyId1'><br>
    <br>
    Ride status pour l'année en cours : <strong>{} h</strong><br><br>
    <img src='cid:MyId0'><br><br>
    gears :<br>{}<br>
    names :<br>{}<br>
    <br>
""".format(total_mtd, total_ytd, unique_gears, unique_names)
mail.Send()
