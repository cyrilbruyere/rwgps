import plotly.express as px

fig = px.scatter(x=[1, 2, 3], y=[3, 1, 6])
fig.write_image("test.png")

print("✅ Fichier test.png généré")