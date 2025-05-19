import plotly.express as px
from pathlib import Path
import os

# 1) Informations sur le dossier courant
cwd = Path.cwd()
print(f"Répertoire courant : {cwd}")

fig = px.scatter(x=[1, 2, 3], y=[3, 1, 6])

# 3) Chemin de sortie (ici, à la racine du dépôt)
out_file = cwd / "test_plot.png"
fig.write_image(out_file)

# 4) Vérifications et affichage
if out_file.exists():
    print("✅ Image générée :", out_file.resolve())
    print("Taille :", out_file.stat().st_size, "octets")
else:
    raise RuntimeError("❌ test_plot.png n’a pas été créé")

# 5) (Optionnel) lister le contenu du dossier pour confirmer
print("\nContenu du dossier :")
for p in cwd.iterdir():
    print(" •", p.name)