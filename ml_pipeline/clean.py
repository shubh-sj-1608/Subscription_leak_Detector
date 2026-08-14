import re


def clean_merchant_text(raw_text):
    text = raw_text.upper()
    text = re.sub(r'\d{4,}', '', text)
    text = re.sub(r'[*#.,]', ' ', text)
    text = re.sub(r'\b(PVT LTD|LTD|LLC|INC|CO|PLC)\b', '', text)
    text = re.sub(r'\b(CA|IN|US|UK)\b', '', text)
    text = re.sub(r'\b(STORE|RETAIL|PURCHASE|GROUP|AND SONS|SUB|MEM|MEMBER)\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_primary_token(text):
    words = text.split()
    return words[0] if words else text


KNOWN_ABBREVIATIONS = {
    "AMZN": "AMAZON",
    "SBUX": "STARBUCKS",
    "MCD": "MCDONALDS",
}


def expand_abbreviations(token):
    return KNOWN_ABBREVIATIONS.get(token, token)


def clean_dataframe(df):
    """Takes a DataFrame with 'raw_merchant_text' column, returns it with cleaning columns added."""
    df = df.copy()
    df["cleaned_text"] = df["raw_merchant_text"].apply(clean_merchant_text)
    df["primary_token"] = df["cleaned_text"].apply(get_primary_token)
    df["primary_token"] = df["primary_token"].apply(expand_abbreviations)
    return df