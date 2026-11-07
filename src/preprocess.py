import re
import pandas as pd

from config import CLEAN_CSV, RAW_CSV


def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,%$-]", "", text)
    return text.strip()


if __name__ == "__main__":
    df = pd.read_csv(RAW_CSV)

    print("Missing values per column:\n", df.isna().sum())
    print("\nDuplicate rows:", df.duplicated().sum())

    df["clean_text"] = df["article_text"].apply(clean_text)
    # The headline carries the main event far more often than the body does
    # (article 1's body says "paused", only the title says "suspended"), so the
    # classifier needs a cleaned title too.
    df["clean_title"] = df["title"].apply(clean_text)
    df = df.drop_duplicates(subset=["title", "clean_text"])
    df["publication_date"] = pd.to_datetime(df["publication_date"])

    df.to_csv(CLEAN_CSV, index=False)
    print(f"\nCleaned {len(df)} articles -> {CLEAN_CSV.relative_to(CLEAN_CSV.parents[2])}")
