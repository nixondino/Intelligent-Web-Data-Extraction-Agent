import re
import pandas as pd


def is_url_or_email(text: str) -> bool:
    """Checks if text is a URL, email, or identifier that shouldn't be split."""
    if not isinstance(text, str):
        return False
    stripped = text.strip()
    if stripped.startswith("http://") or stripped.startswith("https://") or stripped.startswith("ftp://"):
        return True
    if re.match(r"^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$", stripped):
        return True
    if stripped.startswith("10.") and "/" in stripped:  # DOI
        return True
    return False


def clean_text(text: str) -> str:
    """Cleans text strings without breaking URLs, emails, or DOIs."""
    if not isinstance(text, str):
        return text

    text = text.strip()
    if not text:
        return text

    # Preserve URLs, emails, DOIs exactly
    if is_url_or_email(text):
        return text

    # Only add space between lowercase and uppercase if not part of a URL or code snippet
    if not ("http:" in text or "https:" in text or "@" in text):
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        # Add space after sentence punctuation (.!?) only if followed by an uppercase letter
        text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)

    # Collapse multiple consecutive spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple consecutive newlines into double newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def clean_value(value):
    """Recursively cleans values across primitive and nested collections."""
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        cleaned = clean_text(value)
        return cleaned if cleaned != "" else None

    # Recursively clean lists / tuples
    if isinstance(value, (list, tuple)):
        cleaned_list = []
        for item in value:
            cleaned_item = clean_value(item)
            cleaned_list.append(cleaned_item)
        return cleaned_list

    # Recursively clean dictionaries
    if isinstance(value, dict):
        cleaned_dict = {}
        for k, v in value.items():
            clean_k = str(k).strip()
            cleaned_dict[clean_k] = clean_value(v)
        return cleaned_dict

    return value


def clean_dict(data: dict) -> dict:
    """Direct dictionary cleaner preserving unhashable types and None values."""
    if not isinstance(data, dict):
        return {}
    cleaned = {}
    for k, v in data.items():
        cleaned[str(k).strip()] = clean_value(v)
    return cleaned


def clean_data(data: dict) -> pd.DataFrame:
    """
    Cleans extracted dictionary and returns a Pandas DataFrame,
    handling nested lists, dicts, and missing values safely.
    """
    cleaned_dict_data = clean_dict(data)

    # Create DataFrame from the cleaned dictionary
    df = pd.DataFrame([cleaned_dict_data])

    # Ensure empty strings in object columns are replaced with None
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(
                lambda val: None if isinstance(val, str) and val.strip() == "" else val
            )

    return df


if __name__ == "__main__":
    sample = {
        "title": "New Breakthrough in AI",
        "author": "Dr.Jane Doe",
        "date": "2026-03-12",
        "price": 49.99,
        "is_active": True,
        "empty_field": "",
        "none_field": None,
        "source_url": "https://example.com/ai-news",
        "contact_email": "jane.doe@research.edu",
        "doi": "10.1038/s41586-026-0001",
        "categories": ["AI & ML", "Tech", "Robotics"],
        "metadata": {
            "journal": "Nature AI",
            "volume": 12,
            "citations": None
        }
    }

    print("Original:", sample)
    res_df = clean_data(sample)
    cleaned = res_df.to_dict(orient="records")[0]
    print("\nCleaned Result:", cleaned)
    print("URL preserved:", cleaned["source_url"] == "https://example.com/ai-news")
    print("Email preserved:", cleaned["contact_email"] == "jane.doe@research.edu")
    print("Empty field is None:", cleaned["empty_field"] is None)
    print("None field is None:", cleaned["none_field"] is None)