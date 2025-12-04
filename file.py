import pandas as pd
import re

target_sales_experts = ['بابایی', 'احمدی', 'هارونی', 'محمدی']

def clean_phone_number(phone_value):
    # Normalize phone numbers: return 10 digits starting with 9 (remove leading 0 if exists)
    # Iranian mobile numbers must start with 9
    if pd.isna(phone_value):
        return None
    phone_str = str(phone_value)
    digits_only = ''.join(filter(str.isdigit, phone_str))
    if len(digits_only) < 10:
        return None
    
    # If number has 11 digits and starts with 0, remove the 0 to get 10 digits starting with 9
    if len(digits_only) == 11 and digits_only[0] == '0':
        result = digits_only[1:]  # Remove first digit (0) to get 10 digits
        if result[0] == '9':  # Verify it starts with 9
            return result
    
    # If number has 10 digits and starts with 9, return as is
    if len(digits_only) == 10 and digits_only[0] == '9':
        return digits_only
    
    # If number has more than 11 digits, try to find the correct mobile number
    if len(digits_only) > 11:
        # Try to find 11-digit number starting with 0
        last_11 = digits_only[-11:]
        if last_11[0] == '0' and last_11[1] == '9':
            return last_11[1:]  # Remove first digit (0) to get 10 digits starting with 9
        # Try to find 10-digit number starting with 9
        last_10 = digits_only[-10:]
        if last_10[0] == '9':
            return last_10
        # Try to find 10-digit number starting with 9 from different positions
        for i in range(len(digits_only) - 9):
            candidate = digits_only[i:i+10]
            if candidate[0] == '9':
                return candidate
    
    # If number has 10 digits but doesn't start with 9, try to find a valid mobile number
    if len(digits_only) == 10:
        if digits_only[0] == '9':
            return digits_only
        # If it doesn't start with 9, it might be missing the leading 9
        # But we can't add it, so return None or the original
        return None
    
    # For other cases, try to find a 10-digit number starting with 9
    for i in range(len(digits_only) - 9):
        candidate = digits_only[i:i+10]
        if candidate[0] == '9':
            return candidate
    
    return None

def agg_description(series):
    non_null_series = series.dropna()
    if non_null_series.empty:
        return None
    # Concatenate all descriptions with a separator
    return ' | '.join(non_null_series.astype(str))

try:
    df = pd.read_excel('list.xlsx')
except FileNotFoundError:
    print("Excel file not found. Please check the file name.")
    exit()

print("Cleaning and standardizing phone numbers...")
df['numberr'] = df['numberr'].apply(clean_phone_number)
print("Phone number cleaning completed.")
df.dropna(subset=['numberr'], inplace=True)
df['__original_order'] = df.index

product_cols = ['chini', 'dakheli', 'zaban', 'book', 'carman', 'azmoon', 'ghabooli', 'garage', 'hoz', 'kia', 'milyarder', 'gds-tuts','gds','tpms-tuts','zed', 'kmc', 'carmap', 'escl']

# Normalize product columns to 0/1 before aggregation to ensure proper merging
for col in product_cols:
    if col in df.columns:
        numeric_col = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[col] = (numeric_col > 0).astype(int)

# Helper function to check if a name is valid (not empty, not "بدون نام", not NaN, and no digits)
def is_valid_name(name):
    if pd.isna(name):
        return False
    name_str = str(name).strip()
    if not name_str or name_str == '':
        return False
    # Check for common "no name" patterns
    invalid_patterns = ['بدون نام', 'بدوننام', 'نام ندارد', 'نام ندارد', 'nan', 'None', 'null']
    name_lower = name_str.lower()
    for pattern in invalid_patterns:
        if pattern.lower() in name_lower:
            return False
    # Check if name contains digits - if it does, it's not valid
    if re.search(r'\d', name_str):
        return False
    return True

# Compute preferred name per number: 
# 1. Prefer valid names (not empty, not "بدون نام", no digits)
# 2. Then prefer earliest appearance
df['__is_valid_name'] = df['name'].apply(is_valid_name)

# Create name preference map
name_pref_map = (
    df.sort_values(['numberr', '__is_valid_name', '__original_order'], 
                   ascending=[True, False, True])
      .drop_duplicates('numberr', keep='first')
      .set_index('numberr')['name']
)

# For numbers that still have invalid names, try to find any valid name from other rows with same number
def get_best_name_for_number(number, df_subset):
    # Get all names for this number
    names = df_subset[df_subset['numberr'] == number]['name'].dropna()
    valid_names = [name for name in names if is_valid_name(name)]
    
    # Since is_valid_name already checks for digits, all valid_names are without digits
    if valid_names:
        return valid_names[0]
    return None

# Update name_pref_map for numbers with invalid names
for number in name_pref_map.index:
    current_name = name_pref_map[number]
    if not is_valid_name(current_name):
        # Try to find a valid name from all rows with this number
        better_name = get_best_name_for_number(number, df)
        if better_name and is_valid_name(better_name):
            name_pref_map[number] = better_name

aggregation_logic = {
    'name': 'first',
    'sp': 'first',
    'chini': 'max',
    'dakheli': 'max',
    'zaban': 'max',
    'book': 'max',
    'carman': 'max',
    'azmoon': 'max',
    'ghabooli': 'max',
    'garage': 'max',
    'hoz': 'max',
    'kia': 'max',
    'milyarder': 'max',
    'gds-tuts': 'max',
    'gds': 'max',
    'tpms-tuts': 'max',
    'zed': 'max',
    'kmc': 'max',
    'carmap': 'max',
    'escl': 'max',
    # 'maps': 'max',
    'hichi': 'max',
}

# Add description column to aggregation logic if it exists in the dataframe
if 'description' in df.columns:
    aggregation_logic['description'] = agg_description

final_df = df.groupby('numberr').agg(aggregation_logic).reset_index()

# Restore original order based on first appearance in input
order_map = df.drop_duplicates('numberr')[['numberr', '__original_order']]
final_df = final_df.merge(order_map, on='numberr', how='left').sort_values('__original_order').drop(columns='__original_order')

# Ensure sp for each number equals sp from the first occurrence in the original list
first_sp_map = (
    df.sort_values('__original_order')
      .drop_duplicates('numberr', keep='first')
      .set_index('numberr')['sp']
)
final_df['sp'] = final_df['numberr'].map(first_sp_map)

# Ensure name uses the preferred mapping (no digits if available)
final_df['name'] = final_df['numberr'].map(name_pref_map)

# Final check: if any name is still invalid, try to find from original dataframe
print("Filling missing or invalid names from other rows with same number...")
def fill_missing_names(row):
    name = row['name']
    number = row['numberr']
    
    # If name is invalid, search in original dataframe
    if not is_valid_name(name):
        # Get all rows with same number from original dataframe
        same_number_rows = df[df['numberr'] == number]
        valid_names = same_number_rows['name'].apply(is_valid_name)
        valid_name_rows = same_number_rows[valid_names]
        
        if not valid_name_rows.empty:
            # Since is_valid_name already checks for digits, all valid_name_rows are without digits
            return valid_name_rows.iloc[0]['name']
    
    return name

# Count invalid names before filling
invalid_before = final_df['name'].apply(lambda x: not is_valid_name(x)).sum()
final_df['name'] = final_df.apply(fill_missing_names, axis=1)
# Count invalid names after filling
invalid_after = final_df['name'].apply(lambda x: not is_valid_name(x)).sum()
filled_count = invalid_before - invalid_after

if filled_count > 0:
    print(f"Filled {filled_count} missing/invalid names from other rows with same number.")
else:
    print("All names are valid or no replacements found.")

print("Updating 'hichi' column based on new logic...")
# Only use product columns that actually exist in final_df
available_product_cols = [col for col in product_cols if col in final_df.columns]
if available_product_cols:
    final_df['hichi'] = (final_df[available_product_cols].fillna(0).sum(axis=1) == 0).astype(int)
else:
    # If no product columns available, set all to 0 (no products)
    final_df['hichi'] = 0
print("'hichi' column calculation completed.")

# Build human-readable products list based on purchased product flags
product_name_map = {
	'chini': 'دوره آنلاین چینی',
	'dakheli': 'دوره آنلاین داخلی',
	'zaban': 'دوره زبان فنی',
	'book': 'کتاب زبان فنی',
	'carman': 'دستگاه دیاگ',
	'hoz': 'دوره حضوری',
	'kia': 'دوره آنلاین کره ای',
	'milyarder': 'دوره تعمیرکار میلیاردر',
	'gds-tuts': 'دوره GDS',
    'gds': 'نرم افزار GDS',
	'tpms-tuts': 'دوره TPMS',
	'zed': 'دوره ضد سرقت',
	'kmc': 'وبینار KMC',
	'carmap': 'کارمپ',
	'escl': 'فرمان برقی حضوری',
}

def build_products_cell(row):
	selected = []
	for col, pname in product_name_map.items():
		if col in row and pd.notna(row[col]) and int(row[col]) == 1:
			selected.append(pname)
	return ' | '.join(selected)

final_df['products'] = final_df.apply(build_products_cell, axis=1)

# Ensure 'products' is the last column
cols_order = list(final_df.columns)
if 'products' in cols_order:
	cols_order = [c for c in cols_order if c != 'products'] + ['products']
	final_df = final_df[cols_order]

# Keep product columns in output for matrix formation (do not drop them)
# columns_to_drop = [col for col in product_cols if col in final_df.columns]
# final_df = final_df.drop(columns=columns_to_drop)

# Ensure phone numbers are in 10-digit format (starting with 9) in output
def format_phone_10_digits(phone):
    if pd.isna(phone):
        return phone
    phone_str = str(phone)
    digits_only = ''.join(filter(str.isdigit, phone_str))
    # Must be 10 digits starting with 9
    if len(digits_only) == 11 and digits_only[0] == '0' and digits_only[1] == '9':
        return digits_only[1:]  # Remove leading 0 to get 10 digits starting with 9
    if len(digits_only) == 10 and digits_only[0] == '9':
        return digits_only
    # If it's 10 digits but doesn't start with 9, it's invalid - try to find valid number
    if len(digits_only) >= 10:
        # Try to find 10-digit number starting with 9
        for i in range(len(digits_only) - 9):
            candidate = digits_only[i:i+10]
            if candidate[0] == '9':
                return candidate
    return phone_str

final_df['numberr'] = final_df['numberr'].apply(format_phone_10_digits)

# Convert 0 values to empty (NaN) in product columns and hichi - only keep 1 values
for col in product_cols:
    if col in final_df.columns:
        final_df[col] = final_df[col].replace(0, None)

# Convert 0 to empty in hichi column as well
if 'hichi' in final_df.columns:
    final_df['hichi'] = final_df['hichi'].replace(0, None)

final_df.to_excel('final_merged_list.xlsx', index=False)
print("\n'final_merged_list.xlsx' successfully created!")

# Print distribution statistics
print("\n=== Distribution of customers among sales experts ===")
total_customers = len(final_df)
for expert in target_sales_experts:
    count = (final_df['sp'] == expert).sum()
    percentage = (count / total_customers * 100) if total_customers > 0 else 0
    print(f"{expert}: {count} customer ({percentage:.1f}%)")

print(f"\nTotal customers: {total_customers}")
print("Processing completed successfully!")

input("\nPress Enter to close the window...")
