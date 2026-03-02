import pandas as pd
import re
from collections import Counter
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


def clean_and_tokenize(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = text.split()
    tokens = [word for word in tokens if word not in ENGLISH_STOP_WORDS and len(word) > 2]
    return tokens


def word_frequency(df, group_col=None):
    grouped_counts = []

    # default scenario
    if group_col is None:
        counter = Counter()
        for tokens in df['TOKENS']:
            counter.update(tokens)

        for word, count in counter.items():
            if count > 1:
                grouped_counts.append({'WORD': word, 'COUNT': count})

        result = pd.DataFrame(grouped_counts)
        result = result.sort_values(by=['COUNT'], ascending=[False])
        return result.reset_index(drop=True)
    
    # group is provided
    for group, subset in df.groupby(group_col):
        counter = Counter()
        for tokens in subset['TOKENS']:
            counter.update(tokens)

        for word, count in counter.items():
            if count > 1:
                grouped_counts.append({group_col: group, 'WORD': word, 'COUNT': count})

    result = pd.DataFrame(grouped_counts)
    result = result.sort_values(by=[group_col, 'COUNT'], ascending=[True, False])
    return result

    
