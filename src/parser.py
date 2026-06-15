import csv

def parse_csv(csv_content: str) -> list:
    """
    Parses CSV content, skipping first 26 lines, using ';' as delimiter.
    Maps columns:
    Index 0 -> 'Data opercji'
    Index 1 -> 'Opis'
    Index 3 -> 'Kategoria'
    Index 4 -> 'Kwota'
    """
    results = []
    lines = csv_content.splitlines()
    if len(lines) <= 26:
        return results
    
    # Process only from line 27 onwards (0-indexed line 26)
    data_lines = lines[26:]
    csv_reader = csv.reader(data_lines, delimiter=';')
    
    for row in csv_reader:
        if not row:
            continue
        # Ensure row has enough columns (we need at least index 4, so length >= 5)
        if len(row) >= 5:
            mapped_row = {
                "Data opercji": row[0].strip(),
                "Opis": row[1].strip(),
                "Kategoria": row[3].strip(),
                "Kwota": row[4].strip()
            }
            results.append(mapped_row)
    return results
