
import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
df = pd.read_csv(
    "results/age_bmi_diabetes_python.csv",
    dtype={"age_code": str}
)

age_labels = {
    "01": "18–24",
    "02": "25–29",
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

df["age_code"] = df["age_code"].str.zfill(2)
df["age"] = df["age_code"].map(age_labels)
df = df.dropna(subset=["age"])

# Keep all groups, but mark small case counts differently
fig, ax = plt.subplots(figsize=(12, 7))

for category in [1, 2, 3, 4]:
    group = df[df["bmi_category"] == category].sort_values("age_code")

    # Plot all available age groups
    ax.plot(
        group["age"],
        group["percentage"],
        marker="o",
        linewidth=2,
        label=f"BMI category {category}",
    )

    # Highlight groups with fewer than 20 type 2 cases
    small = group[group["small_case_count"] == "YES"]

    ax.scatter(
        small["age"],
        small["percentage"],
        marker="x",
        s=65,
        zorder=3,
    )

ax.set_title("Type 2 Diabetes Percentage by Age and BMI Category")
ax.set_xlabel("Age group (years)")
ax.set_ylabel("Type 2 diabetes (%)")
ax.legend(title="BMI category")
ax.grid(True, alpha=0.3)
plt.xticks(rotation=35)
plt.tight_layout()

plt.savefig("results/bmi_age_comparison.png", dpi=300)
plt.close()

print("Graph saved successfully: results/bmi_age_comparison.png")
print("All BMI categories are included.")
print("An x marker indicates fewer than 20 type 2 cases.")
