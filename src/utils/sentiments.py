import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import nltk
from collections import Counter
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


KEEP_FROM_SKLEARN = {
    "still", "again", "same", "off", "out", "down"
}

SHORT_KEEP = {"ac"}

CUSTOM_EXCLUDE = {
    # pleasantries / email filler
    "thank", "thanks", "hello", "hope",

    # request/admin words
    "contact", "questions", "question", "attached", "detail", "details",
    "info", "information", "request", "requesting", "requester",
    "order", "task", "service", "services", "support", "assist",
    "assistance", "provide", "provided", "generated", "assign",
    "assigned", "caller", "contacted", "regarding", "related",
    "billable", "vendor", "expenses", "charges", "charge", "cost",
    "requisitions", "department", "project", "team", "operations",

    # generic filler verbs / weak words
    "need", "needs", "needed", "like", "just", "make", "made",
    "come", "coming", "go", "going", "get", "gets", "getting",
    "having", "use", "used", "using", "possible", "currently",
    "additional", "following", "good", "let", "know", "look",
    "looks", "want", "really", "able", "appears", "believe",
    "think", "said", "note",

    # weak generic problem words
    "issue", "issues", "problem", "problems",

    # location / orientation words
    "center", "room", "rooms", "floor", "floors", "hall", "hallway",
    "hallways", "office", "offices", "area", "areas", "space",
    "outside", "inside", "near", "located", "location", "main",
    "right", "left", "north", "south", "east", "west", "corner",
    "level", "suite", "basement", "lobby", "entry", "entrance",
    "storage", "closet", "dock", "loading", "station", "courtyard",
    "patio", "garage", "quad", "section", "middle", "rear",
    "building", "buildings", "house", "college", "commons",
    "lab", "classroom", "auditorium", "conference", "lecture",
    "library", "lounge", "servery", "dining", "venue", "campus",
    "university", "shop", "place",

    # time / scheduling words
    "today", "tomorrow", "yesterday", "morning", "afternoon",
    "evening", "night", "day", "days", "week", "weeks",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march", "april",
    "june", "july", "august", "september", "october", "november",
    "december", "jan", "feb", "oct",

    # event / population words
    "event", "meeting", "game", "concert", "football", "annual",
    "student", "students", "staff", "faculty", "people", "public",
    "president", "alumni",

    # contact / communication tokens
    "phone", "email", "ext", "number",

    # restroom location labels that are usually redundant once toilet/restroom/sink stay
    "men", "women", "mens", "womens", "ladies",

    # campus-specific / building-specific terms
    "rice", "edu", "brc", "grb", "dbh", "alm", "coa", "fsc", "rmc", "rupd",
    "duncan", "brown", "baker", "lovett", "fondren", "hanszen",
    "martel", "mcmurtry", "sewall", "wiess", "brockman", "anderson",
    "kraft", "moody", "mcnair", "rawls", "huff", "keck", "ryon",
    "tudor", "garrett", "jones",

    # person names showing up in the counts
    "rodriguez", "monica", "frydl", "juan", "david", "matt", "garcia",
    "munira", "vejlani", "olivia", "james", "dewayne", "sid", "allen",
    "mosquinski", "bradley", "calvin", "abbatessa", "gutierrez",
    "brad", "thang", "anh", "mike", "maria", "francisco", "rudy",
    "hannes", "jonathan", "sanchez", "minh", "harper", "urbano",
    "nguyen", "benny", "waldron", "thacker", "layton", "herring",
    "connor", "tegan", "tegang",

    # tokenization artifacts
    "doesn", "isn", "won", "don", "didn", "aren", "wasn", "weren",
    "hasn", "haven", "couldn", "wouldn", "shouldn", "attn", "xxxx"
}

STOP_WORDS = (set(ENGLISH_STOP_WORDS) - KEEP_FROM_SKLEARN) | CUSTOM_EXCLUDE

nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def sentiment_score(text):
    text = clean_text(text)
    if text == "":
        return np.nan
    return sia.polarity_scores(text)["compound"]


def print_sentiment_extremes(df, text_col, sentiment_col=None, n=5):
    if sentiment_col is None:
        sentiment_col = f"{text_col}_SENTIMENT"

    cols_to_show = ["WORK_TASK_ID", "SERVICE_CLASS", "REQUEST_CLASS", text_col, sentiment_col]
    available_cols = [col for col in cols_to_show if col in df.columns]

    top_rows = (
        df[available_cols]
        .dropna(subset=[sentiment_col])
        .sort_values(sentiment_col, ascending=False)
        .head(n)
    )

    bottom_rows = (
        df[available_cols]
        .dropna(subset=[sentiment_col])
        .sort_values(sentiment_col, ascending=True)
        .head(n)
    )

    print(f"Top {n} {text_col} sentiment")
    for _, row in top_rows.iterrows():
        for col in available_cols:
            print(f"{col}: {row[col]}")
        print("-" * 120)

    print(f"\nBottom {n} {text_col} sentiment")
    for _, row in bottom_rows.iterrows():
        for col in available_cols:
            print(f"{col}: {row[col]}")
        print("-" * 120)


def clean_and_tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)  # remove punctuation/numbers
    tokens = text.split()
    tokens = [word for word in tokens
              if word not in STOP_WORDS and len(word) > 2
                or word in SHORT_KEEP]
    return tokens


def word_frequency(df, group_col=None, group_value=None):
    grouped_counts = []

    # Default
    if group_col == None:
        counter = Counter()
        for tokens in df["TOKENS"]:
            counter.update(tokens)

        for word, count in counter.items():
            if count > 1:
                grouped_counts.append({"WORD": word, "COUNT": count})

    # Grouped
    else:
        if group_value != None:
            df = df[df[group_col] == group_value]

        for group, subset in df.groupby(group_col):
            counter = Counter()
            for tokens in subset["TOKENS"]:
                counter.update(tokens)

            for word, count in counter.items():
                if count > 1:
                    grouped_counts.append({group_col: group, "WORD": word, "COUNT": count})

    result = pd.DataFrame(grouped_counts)
    if group_col != None and group_value == None:
        result = result.sort_values(by=[group_col, "COUNT"], ascending=[True, False])
    else:
        result = result.sort_values(by=["COUNT"], ascending=False)

    return result.reset_index(drop=True)


def top_n_words_per_group(df, group_col, n=5, output_csv=None, group_value=None):
    # Get word counts using your existing function
    wf = word_frequency(df, group_col=group_col, group_value=group_value)

    # If filtering to one specific group value, just take the top n overall
    if group_value is not None:
        result = wf.sort_values("COUNT", ascending=False).head(n).reset_index(drop=True)
    else:
        # For each unique value in group_col, take top n words by COUNT
        result = (
            wf.sort_values([group_col, "COUNT"], ascending=[True, False])
              .groupby(group_col, group_keys=False)
              .head(n)
              .reset_index(drop=True)
        )

    # Save if requested
    if output_csv is not None:
        result.to_csv(output_csv, index=False)

    return result


def get_top_groups_by_volume(df, group_col, top_k=5):
    return (
        df[group_col]
        .dropna()
        .astype(str)
        .value_counts()
        .head(top_k)
        .index
        .tolist()
    )

def get_top_words_for_top_groups(df, group_col, top_k_groups=5, n_words=5):
    top_groups = get_top_groups_by_volume(df, group_col, top_k=top_k_groups)

    top_words = top_n_words_per_group(df, group_col=group_col, n=n_words).copy()
    top_words[group_col] = top_words[group_col].astype(str)
    top_words = top_words[top_words[group_col].isin(top_groups)].reset_index(drop=True)

    return top_groups, top_words

def plot_top_word_bars(top_words_df, group_col, figsize=(14, 10)):
    groups = top_words_df[group_col].dropna().unique().tolist()
    if not groups:
        print(f"No data to plot for {group_col}.")
        return

    fig, axes = plt.subplots(len(groups), 1, figsize=figsize)
    if len(groups) == 1:
        axes = [axes]

    for ax, group in zip(axes, groups):
        subset = (
            top_words_df[top_words_df[group_col] == group]
            .sort_values("COUNT", ascending=True)
        )
        ax.barh(subset["WORD"], subset["COUNT"])
        ax.set_title(str(group))
        ax.set_xlabel("Count")
        ax.set_ylabel("Word")

    plt.tight_layout()
    plt.show()

def plot_top_word_heatmap(top_words_df, group_col, top_groups, normalize=True, figsize=(10, 6)):
    heatmap_df = (
        top_words_df.pivot_table(
            index="WORD",
            columns=group_col,
            values="COUNT",
            aggfunc="sum",
            fill_value=0
        )
        .reindex(columns=top_groups, fill_value=0)
    )

    if normalize:
        heatmap_df = heatmap_df.div(heatmap_df.sum(axis=0).replace(0, 1), axis=1)

    plt.figure(figsize=figsize)
    plt.imshow(heatmap_df.values, aspect="auto")
    plt.colorbar(label="Normalized Frequency" if normalize else "Count")
    plt.xticks(range(len(heatmap_df.columns)), heatmap_df.columns, rotation=45, ha="right")
    plt.yticks(range(len(heatmap_df.index)), heatmap_df.index)
    plt.title(f"Top Words Across High-Volume {group_col} Categories")
    plt.xlabel(group_col)
    plt.ylabel("Word")
    plt.tight_layout()
    plt.show()

    return heatmap_df