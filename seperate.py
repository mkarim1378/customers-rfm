import pandas as pd

INPUT_FILE = 'final_merged_list.xlsx'
OUTPUT_FILE = 'products_long.xlsx'

PRODUCT_COLS = [
    'chini', 'dakheli', 'zaban', 'book', 'carman', 'azmoon', 'ghabooli',
    'garage', 'hoz', 'kia', 'milyarder', 'gds', 'tpms-tuts', 'zed'
]

PRODUCT_PERSIAN = {
    'chini': 'آنلاین چینی',
    'dakheli': 'آنلاین داخلی',
    'zaban': 'دوره زبان فنی',
    'book': 'کتاب زبان فنی',
    'carman': 'دستگاه',
    'azmoon': 'آزمون',
    'ghabooli': 'قبولی در آزمون',
    'garage': 'کارنو گاراژ',
    'hoz': 'دوره حضوری',
    'kia': 'کیا و هیوندای',
    'milyarder': 'تعمیرکار میلیاردر',
    'gds': 'دوره GDS',
    'tpms-tuts': 'دوره TPMS',
    'zed': 'دوره ضد سرقت',
}


def clean_phone_number(phone_value):
    if pd.isna(phone_value):
        return None
    s = str(phone_value)
    digits = ''.join(ch for ch in s if ch.isdigit())
    if len(digits) < 10:
        return None
    return digits[-10:]


def main():
    try:
        df = pd.read_excel(INPUT_FILE)
    except FileNotFoundError:
        print('Input Excel file not found:', INPUT_FILE)
        return

    # Normalize phone numbers
    if 'numberr' not in df.columns:
        print("Column 'numberr' not found in input file.")
        return
    df['numberr'] = df['numberr'].apply(clean_phone_number)
    df = df[df['numberr'].notna()].copy()

    # Ensure product flags are numeric 0/1
    for col in PRODUCT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = (df[col] > 0).astype(int)
        else:
            # If a product column is missing, create it as zeros
            df[col] = 0

    long_rows = []
    for _, row in df.iterrows():
        name = row.get('name')
        number = row.get('numberr')
        sp = row.get('sp')

        # Collect rows for each purchased product
        added_any = False
        for col in PRODUCT_COLS:
            if row[col] == 1:
                long_rows.append({
                    'name': name,
                    'numberr': number,
                    'sp': sp,
                    'product': PRODUCT_PERSIAN[col]
                })
                added_any = True

        # If no product flags, still emit one row (at least one per input row)
        if not added_any:
            long_rows.append({
                'name': name,
                'numberr': number,
                'sp': sp,
                'product': 'بدون محصول'
            })

    out_df = pd.DataFrame(long_rows, columns=['name', 'numberr', 'sp', 'product'])
    out_df.to_excel(OUTPUT_FILE, index=False)
    print(f"Created {OUTPUT_FILE} with {len(out_df)} rows.")


if __name__ == '__main__':
    main()


