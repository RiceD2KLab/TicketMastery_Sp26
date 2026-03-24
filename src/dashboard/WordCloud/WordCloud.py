import pandas as pd
import re
from collections import Counter
from dashboard.WordCloud.StopWords import STOP_WORDS, SHORT_KEEP

"""
    Normalize and tokenize free-text descriptions for downstream word-frequency analysis.
    Args:
        text (str): Raw text to clean and tokenize.

    Returns:
        list[str]: Ordered list of filtered tokens.
    """
def clean_and_tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text) 
    tokens = text.split()
    tokens = [word for word in tokens
              if word not in STOP_WORDS and len(word) > 2 
                or word in SHORT_KEEP]
    return tokens

"""
Compute word frequencies from a tokenized DataFrame, optionally by group.
Note: No longer in use

Args:
    df (pd.DataFrame): DataFrame containing a TOKENS column.
    group_col (str | None, optional): Column name used to group word counts.
        Defaults to None.
    group_value (str | None, optional): Specific value within group_col to filter
        to before aggregation. Defaults to None.

Returns:
    pd.DataFrame: DataFrame of word counts with columns:
        - ["WORD", "COUNT"] for overall counts
        - [group_col, "WORD", "COUNT"] for grouped counts
"""
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