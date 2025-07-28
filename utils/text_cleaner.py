import re 

def split_clean_lines(text):
    # Replace all non-breaking spaces with space
    text = text.replace('\xa0', ' ')
    # Collapse multiple newlines into a single newline
    text = re.sub(r'\n+', '\n', text)
    # Optionally: strip leading/trailing whitespace
    text = text.strip()
    # Split by newline
    lines = text.split('\n')
    # Remove any lines that are just whitespace or empty
    lines = [line.strip() for line in lines if line.strip()]
    return lines


def clean_number_from_special_characters(number_str):
    numeric_string = ''.join(re.findall(r'\d+', number_str))
    return numeric_string

def extract_currency_and_amount(text):
    # Match a sequence of letters (currency code) followed by digits (amount)
    match = re.match(r'([A-Za-z]+)([\d.,]+)', text.strip())
    if match:
        currency = match.group(1)
        amount = match.group(2).replace(',', '')  # Remove commas if any
        return currency, amount
    else:
        return None, None
