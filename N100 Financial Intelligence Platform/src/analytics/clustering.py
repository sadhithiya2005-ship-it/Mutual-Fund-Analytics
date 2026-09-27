from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[2]

COMPANIES_FILE = BASE_DIR / "data" / "raw" / "companies.xlsx"
SECTORS_FILE = BASE_DIR / "data" / "raw" / "sectors.xlsx"
RATIOS_FILE = BASE_DIR / "output" / "financial_ratios_engineered.csv"
CAGR_FILE = BASE_DIR / "output" / "cagr_features.csv"

OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"

CLUSTER_OUTPUT = OUTPUT_DIR / "cluster_labels.csv"
PROFILE_OUTPUT = OUTPUT_DIR / "cluster_profiles.csv"
CORRELATION_OUTPUT = OUTPUT_DIR / "kpi_correlation.csv"
ELBOW_PLOT = REPORTS_DIR / "elbow_plot.png"


FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def load_data():
    """Load company, sector, ratio and CAGR datasets."""

    companies = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    sectors = pd.read_excel(
        SECTORS_FILE,
        header=0,
    )

    ratios = pd.read_csv(
        RATIOS_FILE,
    )

    cagr = pd.read_csv(
        CAGR_FILE,
    )

    companies["id"] = companies["id"].astype(str).str.strip()
    sectors["company_id"] = sectors["company_id"].astype(str).str.strip()
    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    cagr["company_id"] = cagr["company_id"].astype(str).str.strip()

    return companies, sectors, ratios, cagr


def prepare_dataset(companies, sectors, ratios, cagr):
    """Prepare one latest-year feature row for each N100 company."""

    n100 = companies[
        ["id", "company_name"]
    ].copy()

    n100 = n100.rename(
        columns={
            "id": "company_id",
        }
    )

    n100["company_id"] = (
        n100["company_id"]
        .astype(str)
        .str.strip()
    )

    ratios["year_num"] = (
        ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )

    ratios["year_num"] = pd.to_numeric(
        ratios["year_num"],
        errors="coerce",
    )

    # Select the latest available financial-ratio
    # record for each company.
    ratios_latest = (
        ratios.sort_values("year_num")
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    ratio_features = ratios_latest[
        [
            "company_id",
            "return_on_equity_pct",
            "debt_to_equity",
            "operating_profit_margin_pct",
        ]
    ].copy()

    result = n100.merge(
        ratio_features,
        on="company_id",
        how="left",
    )

    result = result.merge(
        cagr[
            [
                "company_id",
                "revenue_cagr_5yr",
                "fcf_cagr_5yr",
            ]
        ],
        on="company_id",
        how="left",
    )

    result = result.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
            ]
        ],
        on="company_id",
        how="left",
    )

    return result


def sector_median_imputation(df):
    """Fill missing clustering features using sector medians."""

    df = df.copy()

    for feature in FEATURES:

        df[feature] = pd.to_numeric(
            df[feature],
            errors="coerce",
        )

        sector_median = (
            df.groupby("broad_sector")[feature]
            .transform("median")
        )

        df[feature] = df[feature].fillna(
            sector_median
        )

        # Final fallback if a sector has no
        # valid value for this feature.
        df[feature] = df[feature].fillna(
            df[feature].median()
        )

    return df


def create_elbow_plot(X_scaled):
    """Create KMeans elbow plot."""

    inertias = []

    for k in range(2, 10):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        model.fit(X_scaled)

        inertias.append(
            model.inertia_
        )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        range(2, 10),
        inertias,
        marker="o",
    )

    plt.xlabel(
        "Number of Clusters"
    )

    plt.ylabel(
        "Inertia"
    )

    plt.title(
        "KMeans Elbow Plot"
    )

    plt.tight_layout()

    plt.savefig(
        ELBOW_PLOT,
        dpi=150,
    )

    plt.close()


def assign_cluster_names(df):
    """Assign unique descriptive names to the five clusters."""

    names = {
        0: "Stable Quality",
        1: "High Growth & High Leverage",
        2: "Strong Cash Generation",
        3: "Exceptional Margin Outlier",
        4: "Growth & Profitability",
    }

    return names


def run_clustering(df):
    """Scale features and run five-cluster KMeans."""

    X = df[FEATURES].copy()

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    create_elbow_plot(
        X_scaled
    )

    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10,
    )

    cluster_ids = model.fit_predict(
        X_scaled
    )

    df["cluster_id"] = cluster_ids

    distances = model.transform(
        X_scaled
    )

    df["distance_from_centroid"] = (
        distances.min(axis=1)
    )

    cluster_names = assign_cluster_names(
        df
    )

    df["cluster_name"] = (
        df["cluster_id"]
        .map(cluster_names)
    )

    return df, model


def create_cluster_profile(df):
    """Create mean and median profiles for each cluster."""

    mean_profile = (
        df.groupby("cluster_id")[FEATURES]
        .mean()
        .add_suffix("_mean")
    )

    median_profile = (
        df.groupby("cluster_id")[FEATURES]
        .median()
        .add_suffix("_median")
    )

    profile = (
        mean_profile
        .join(median_profile)
        .reset_index()
    )

    profile.to_csv(
        PROFILE_OUTPUT,
        index=False,
    )


def create_correlation_matrix(df):
    """Create Pearson correlation matrix for clustering KPIs."""

    correlation = df[
        FEATURES
    ].corr(
        method="pearson"
    )

    correlation.to_csv(
        CORRELATION_OUTPUT
    )


def main():
    """Run complete Sprint 6 clustering pipeline."""

    print("Loading data...")

    companies, sectors, ratios, cagr = (
        load_data()
    )

    print(
        "Preparing clustering dataset..."
    )

    df = prepare_dataset(
        companies,
        sectors,
        ratios,
        cagr,
    )

    print(
        f"Companies before imputation: {len(df)}"
    )

    print(
        "Applying sector median imputation..."
    )

    df = sector_median_imputation(
        df
    )

    print(
        "Running KMeans clustering..."
    )

    df, model = run_clustering(
        df
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].to_csv(
        CLUSTER_OUTPUT,
        index=False,
    )

    create_cluster_profile(
        df
    )

    create_correlation_matrix(
        df
    )

    print(
        "\nClustering completed."
    )

    print(
        f"Companies: {len(df)}"
    )

    print(
        f"Clusters: {df['cluster_id'].nunique()}"
    )

    print(
        "\nCluster counts:"
    )

    print(
        df[
            "cluster_name"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(
        "\nCluster ID mapping:"
    )

    print(
        df[
            [
                "cluster_id",
                "cluster_name",
            ]
        ]
        .drop_duplicates()
        .sort_values("cluster_id")
        .to_string(index=False)
    )

    print(
        "\nOutput files:"
    )

    print(
        CLUSTER_OUTPUT
    )

    print(
        PROFILE_OUTPUT
    )

    print(
        CORRELATION_OUTPUT
    )

    print(
        ELBOW_PLOT
    )


if __name__ == "__main__":
    main()