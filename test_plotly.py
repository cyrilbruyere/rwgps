import plotly.express as px
import plotly.io as pio
import plotly
import os

print("✅ Plotly version :", plotly.__version__)
print("✅ Backend de rendu :", pio.renderers.default)

# 🔍 Vérifie si Kaleido fonctionne
try:
    _ = pio.kaleido.scope
    print("✅ Kaleido est disponible")
except Exception as e:
    print("❌ Kaleido est manquant ou non fonctionnel :", e)

# 🖼️ Test de génération de fichier
fig = px.scatter(x=[1, 2, 3], y=[4, 5, 6])
fig.write_image("test_plot.png")

if os.path.exists("test_plot.png"):
    print("✅ test_plot.png a été créé avec succès.")
else:
    raise RuntimeError("❌ test_plot.png n’a pas été créé.")