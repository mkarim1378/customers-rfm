import flet as ft
import pandas as pd
import os
import threading

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

def process_customer_list(file_path, progress_callback=None, status_callback=None):
    """Process the customer list file and return the final dataframe"""
    
    if status_callback:
        status_callback("Reading Excel file...")
    
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        raise Exception("Excel file not found. Please check the file name.")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")
    
    if status_callback:
        status_callback("Cleaning and standardizing phone numbers...")
    
    df['numberr'] = df['numberr'].apply(clean_phone_number)
    df.dropna(subset=['numberr'], inplace=True)
    df['__original_order'] = df.index

    product_cols = ['chini', 'dakheli', 'zaban', 'book', 'carman', 'azmoon', 'ghabooli', 'garage', 'hoz', 'kia', 'milyarder', 'gds','tpms-tuts','zed', 'kmc', 'carmap', 'escl']

    # Normalize product columns to 0/1 before aggregation to ensure proper merging
    if status_callback:
        status_callback("Normalizing product columns...")
    
    for col in product_cols:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = (numeric_col > 0).astype(int)

    # Compute preferred name per number: prefer names without digits, then earliest appearance
    df['__name_no_digit'] = ~df['name'].astype(str).str.contains(r'\d')
    name_pref_map = (
        df.sort_values(['numberr', '__name_no_digit', '__original_order'], ascending=[True, False, True])
          .drop_duplicates('numberr', keep='first')
          .set_index('numberr')['name']
    )

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
        'gds': 'max',
        'tpms-tuts': 'max',
        'zed': 'max',
        'kmc': 'max',
        'carmap': 'max',
        'escl': 'max',
        'hichi': 'max',
    }

    # Add description column to aggregation logic if it exists in the dataframe
    if 'description' in df.columns:
        aggregation_logic['description'] = agg_description

    if status_callback:
        status_callback("Merging duplicate records...")
    
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

    if status_callback:
        status_callback("Updating 'hichi' column...")
    
    final_df['hichi'] = (final_df[product_cols].fillna(0).sum(axis=1) == 0).astype(int)

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
        'gds': 'دوره GDS',
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

    if status_callback:
        status_callback("Building products list...")
    
    final_df['products'] = final_df.apply(build_products_cell, axis=1)

    # Ensure 'products' is the last column
    cols_order = list(final_df.columns)
    if 'products' in cols_order:
        cols_order = [c for c in cols_order if c != 'products'] + ['products']
        final_df = final_df[cols_order]

    # Ensure phone numbers are in 10-digit format (starting with 9) in output
    if status_callback:
        status_callback("Formatting phone numbers...")
    
    final_df['numberr'] = final_df['numberr'].apply(format_phone_10_digits)

    # Convert 0 values to empty (NaN) in product columns and hichi - only keep 1 values
    for col in product_cols:
        if col in final_df.columns:
            final_df[col] = final_df[col].replace(0, None)

    # Convert 0 to empty in hichi column as well
    if 'hichi' in final_df.columns:
        final_df['hichi'] = final_df['hichi'].replace(0, None)

    if status_callback:
        status_callback("Saving output file...")
    
    # Save to final_merged_list.xlsx in the same directory as input file
    output_dir = os.path.dirname(file_path) if os.path.dirname(file_path) else '.'
    output_path = os.path.join(output_dir, 'final_merged_list.xlsx')
    final_df.to_excel(output_path, index=False)
    
    if status_callback:
        status_callback("Processing completed successfully!")
    
    return final_df

def main(page: ft.Page):
    page.title = "Customer List Processor"
    page.window.width = 1200
    page.window.height = 800
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # State variables
    selected_file_path = None
    processed_data = None
    
    # UI Components
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    
    file_path_text = ft.Text("No file selected", size=14, color=ft.Colors.GREY_700)
    status_text = ft.Text("Ready", size=12, color=ft.Colors.BLUE_700)
    progress_bar = ft.ProgressBar(width=400, visible=False)
    
    # Data table
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Phone")),
            ft.DataColumn(ft.Text("Name")),
            ft.DataColumn(ft.Text("Sales Expert")),
            ft.DataColumn(ft.Text("Products")),
        ],
        rows=[],
    )
    
    scrollable_table = ft.Container(
        content=ft.Column(
            controls=[data_table],
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
    )
    
    def file_picked(e):
        nonlocal selected_file_path
        if e.files and len(e.files) > 0:
            selected_file_path = e.files[0].path
            file_path_text.value = os.path.basename(selected_file_path)
            file_path_text.color = ft.Colors.GREEN_700
            status_text.value = "File selected. Click 'Process' to continue."
            status_text.color = ft.Colors.BLUE_700
            page.update()
    
    file_picker.on_result = file_picked
    
    def select_file(e):
        file_picker.pick_files(
            dialog_title="Select Excel file",
            allowed_extensions=["xlsx", "xls"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
    
    def process_file(e):
        nonlocal processed_data
        
        if not selected_file_path:
            status_text.value = "Please select a file first!"
            status_text.color = ft.Colors.RED_700
            page.update()
            return
        
        # Disable process button and show progress
        process_btn.disabled = True
        select_btn.disabled = True
        progress_bar.visible = True
        status_text.value = "Processing..."
        status_text.color = ft.Colors.BLUE_700
        data_table.rows = []
        page.update()
        
        def process_in_thread():
            nonlocal processed_data
            try:
                def update_status(msg):
                    status_text.value = msg
                    page.update()
                
                processed_data = process_customer_list(
                    selected_file_path,
                    status_callback=update_status
                )
                
                # Update UI directly (page.update() is thread-safe)
                update_ui_after_processing()
                
            except Exception as ex:
                show_error(str(ex))
        
        def update_ui_after_processing():
            nonlocal processed_data
            # Clear existing rows
            data_table.rows = []
            
            # Add rows from processed data
            for idx, row in processed_data.iterrows():
                phone = str(row.get('numberr', ''))
                name = str(row.get('name', ''))
                sp = str(row.get('sp', ''))
                products = str(row.get('products', ''))
                
                data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(phone)),
                            ft.DataCell(ft.Text(name)),
                            ft.DataCell(ft.Text(sp)),
                            ft.DataCell(ft.Text(products)),
                        ]
                    )
                )
            
            # Re-enable buttons and hide progress
            process_btn.disabled = False
            select_btn.disabled = False
            progress_bar.visible = False
            status_text.value = f"Processing completed! {len(processed_data)} customers processed."
            status_text.color = ft.Colors.GREEN_700
            page.update()
        
        def show_error(error_msg):
            process_btn.disabled = False
            select_btn.disabled = False
            progress_bar.visible = False
            status_text.value = f"Error: {error_msg}"
            status_text.color = ft.Colors.RED_700
            page.update()
        
        # Run processing in background thread
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()
    
    select_btn = ft.ElevatedButton(
        "Select File",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=select_file,
    )
    
    process_btn = ft.ElevatedButton(
        "Process",
        icon=ft.Icons.PLAY_ARROW,
        on_click=process_file,
    )
    
    # Layout
    page.add(
        ft.Row(
            controls=[
                ft.Text("Customer List Processor", size=24, weight=ft.FontWeight.BOLD),
            ],
        ),
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Row(
            controls=[
                select_btn,
                process_btn,
            ],
        ),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        ft.Row(
            controls=[
                ft.Text("Selected file: ", size=14, weight=ft.FontWeight.W_500),
                file_path_text,
            ],
        ),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        ft.Row(
            controls=[
                progress_bar,
            ],
        ),
        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
        status_text,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        ft.Text("Processed Customers:", size=16, weight=ft.FontWeight.BOLD),
        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
        scrollable_table,
    )

if __name__ == "__main__":
    ft.app(target=main)

