
import pandas as pd
import matplotlib.pyplot as plt

# Lire les résultats déjà calculés avec Bash
df = pd.read_csv("results/age_bmi_diabetes.csv")

# Garder la catégorie BMI 4 (obésité)
# et les groupes avec au moins 20 cas de type 2
obesity = df[
    (df["bmi_category"] == 4)
    & (df["small_case_count"] == "NO")
].copy()

# Associer chaque code d'âge à son intervalle
age_labels = {
    "03": "30–34",
    "04": "35–39",
    "05": "40–44",
    "06": "45–49",
    "07": "50–54",
    "08": "55–59",
    "09": "60–64",
    "10": "65–69",
    "11": "70–74",
    "12": "75–79",
    "13": "80+",
}

obesity["age_code"] = obesity["age_code"].astype(str).str.zfill(2)
obesity["age"] = obesity["age_code"].map(age_labels)
obesity = obesity.dropna(subset=["age"])

# Tracer le graphique
plt.figure(figsize=(10, 6))
plt.plot(
    obesity["age"],
    obesity["percentage"],
    marker="o"
)

plt.title("Type 2 Diabetes Percentage by Age — Obesity Category")
plt.xlabel("Age group (years)")
plt.ylabel("Type 2 diabetes (%)")
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Enregistrer le graphique
plt.savefig("results/obesity_age.png", dpi=300)
plt.close()
print("Graph saved successfully: results/obesity_age.png")
