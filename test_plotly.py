import plotly.express as px
import plotly.io as pio
import plotly
import os

print("✅ Plotly version :", plotly.__version__)
print("✅ Backend de rendu :", pio.renderers.default)

# 🔧 Forcer kaleido
pio.renderers.default = "kaleido"

try:
    _ = pio.kaleido.scope
    print("✅ Kaleido est fonctionnel")
except Exception as e:
    print("❌ Kaleido pose problème :", e)

# 📈 Création du graphique
fig = px.scatter(x=[1, 2, 3], y=[4, 5, 6])

# 🖼️ Tentative d’écriture avec catch des erreurs
try:
    fig.write_image("test_plot.png")
    if os.path.exists("test_plot.png"):
        print("✅ test_plot.png a été créé avec succès.")
    else:
        raise RuntimeError("❌ test_plot.png n’a pas été créé.")
except Exception as e:
    print("❌ Erreur pendant write_image :", e)
    raise