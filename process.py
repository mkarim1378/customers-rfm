import pandas as pd

input_file = 'listt.xlsx'
df = pd.read_excel(input_file)

def fix_phone(phone):
    if pd.isna(phone):
        return None
    phone = str(phone)
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 10:
        return phone
    return digits[-10:]

df['mobile'] = df['billing_phone'].apply(fix_phone)
df = df[df['mobile'].notna()]

df['full_name'] = df['billing_first_name'].astype(str) + ' ' + df['billing_last_name'].astype(str)

df['order_index'] = df.reset_index().index

line_item_cols = ['line_item_1', 'line_item_2', 'line_item_3', 'line_item_4']
df_melted = df.melt(
    id_vars=['order_index', 'mobile', 'full_name'],
    value_vars=line_item_cols,
    var_name='line_item_num',
    value_name='product_name'
)

df_melted = df_melted[df_melted['product_name'].notna() & (df_melted['product_name'] != '')]

df_melted['line_item_num'] = df_melted['line_item_num'].str.extract(r'(\d+)').astype(int)
df_melted = df_melted.sort_values(['order_index', 'line_item_num'])

output_df = df_melted[['mobile', 'full_name', 'product_name']]

output_file = 'orders_processed.xlsx'
output_df.to_excel(output_file, index=False)

print(f'Output file saved as {output_file}.')
input("\nPress Enter to close the window...")
