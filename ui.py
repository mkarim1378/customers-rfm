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
        status_callback("Processing completed successfully!")
    
    return final_df

def main(page: ft.Page):
    page.title = "Carno Academy Super RFM"
    page.window.width = page.window.max_width
    page.window.height = page.window.max_height
    page.window.maximized = True
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Set window icon and logo (try different possible names)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = None
    logo_path = None
    possible_logo_names = ["icon.ico", "logo.png", "logo.jpg", "logo.ico", "icon.png"]
    for logo_name in possible_logo_names:
        test_path = os.path.join(base_dir, logo_name)
        if os.path.exists(test_path):
            if logo_name.endswith('.ico'):
                icon_path = test_path
            if not logo_path:  # Use first found as logo
                logo_path = test_path
            break
    
    # Set window icon
    if icon_path:
        try:
            page.window.icon = icon_path
        except:
            pass
    
    # State variables
    selected_file_path = None
    selected_output_path = None
    processed_data = None
    file_info = None
    
    # UI Components
    file_picker = ft.FilePicker()
    save_file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    page.overlay.append(save_file_picker)
    
    # Drag and drop area (clickable container)
    drag_drop_container = ft.Container(
        width=500,
        height=300,
        border=ft.border.all(2, ft.Colors.GREY_400),
        border_radius=10,
        bgcolor=ft.Colors.GREY_50,
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.CLOUD_UPLOAD, size=64, color=ft.Colors.BLUE_400),
                ft.Text("Drag & Drop your Excel file here", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                ft.Text("or click to browse", size=14, color=ft.Colors.GREY_600),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        ),
        on_click=lambda e: select_file(e),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )
    
    def on_hover_drag_box(e):
        if e.data == "true":
            drag_drop_container.border = ft.border.all(3, ft.Colors.BLUE_400)
            drag_drop_container.bgcolor = ft.Colors.BLUE_50
        else:
            if selected_file_path is None:
                drag_drop_container.border = ft.border.all(2, ft.Colors.GREY_400)
                drag_drop_container.bgcolor = ft.Colors.GREY_50
        page.update()
    
    drag_drop_container.on_hover = on_hover_drag_box
    
    # File info display
    file_info_container = ft.Container(
        visible=False,
        content=ft.Column(
            controls=[],
            spacing=10,
        ),
    )
    
    # Loading spinner
    loading_spinner = ft.ProgressRing(
        width=80,
        height=80,
        stroke_width=4,
        visible=False,
    )
    
    status_text = ft.Text("Ready to process! 🚀", size=16, color=ft.Colors.BLUE_700, weight=ft.FontWeight.W_500)
    
    # Logo
    logo_image = None
    if logo_path:
        try:
            # Use absolute path for image
            abs_logo_path = os.path.abspath(logo_path)
            logo_image = ft.Image(
                src=abs_logo_path,
                width=120,
                height=120,
                fit=ft.ImageFit.CONTAIN,
            )
        except Exception as e:
            print(f"Error loading logo: {e}")
            logo_image = None
    
    # Data table
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#")),
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
        visible=False,
    )
    
    def get_file_size(file_path):
        """Get file size in human readable format"""
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def handle_file_selection(file_path):
        nonlocal selected_file_path, file_info
        selected_file_path = file_path
        file_name = os.path.basename(selected_file_path)
        file_size = get_file_size(selected_file_path)
        
        # Update drag drop container to show file info
        drag_drop_container.content.controls = [
            ft.Icon(ft.Icons.CHECK_CIRCLE, size=64, color=ft.Colors.GREEN_500),
            ft.Text(f"File loaded! ✨", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
            ft.Text(f"{file_name}", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
            ft.Text(f"Size: {file_size}", size=12, color=ft.Colors.GREY_600),
        ]
        drag_drop_container.border = ft.border.all(2, ft.Colors.GREEN_400)
        drag_drop_container.bgcolor = ft.Colors.GREEN_50
        
        status_text.value = "Great! Processing your file now... ⚡"
        status_text.color = ft.Colors.BLUE_700
        
        # Show loading spinner and start processing
        loading_spinner.visible = True
        page.update()
        
        # Auto-start processing
        start_processing()
    
    def file_picked(e):
        if e.files and len(e.files) > 0:
            handle_file_selection(e.files[0].path)
    
    # Enable file picker to accept dropped files
    file_picker.on_result = file_picked
    
    def output_path_selected(e):
        nonlocal selected_output_path
        if e.path:
            selected_output_path = e.path
            status_text.value = f"Output path set! Ready to export 🎯"
            status_text.color = ft.Colors.GREEN_700
            page.update()
    
    save_file_picker.on_result = output_path_selected
    
    def select_file(e):
        file_picker.pick_files(
            dialog_title="Select Excel file",
            allowed_extensions=["xlsx", "xls"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
    
    def select_output_path(e):
        save_file_picker.save_file(
            dialog_title="Save output file",
            file_name="final_merged_list.xlsx",
            allowed_extensions=["xlsx"],
        )
    
    def start_processing():
        nonlocal processed_data
        
        if not selected_file_path:
            return
        
        def process_in_thread():
            nonlocal processed_data
            try:
                def update_status(msg):
                    # Update status with fun messages
                    fun_messages = {
                        "Reading Excel file...": "Reading your file... 📖",
                        "Cleaning and standardizing phone numbers...": "Cleaning up phone numbers... 🧹",
                        "Normalizing product columns...": "Organizing products... 📦",
                        "Merging duplicate records...": "Merging duplicates... 🔄",
                        "Updating 'hichi' column...": "Finalizing data... ✨",
                        "Building products list...": "Building product list... 🏗️",
                        "Formatting phone numbers...": "Formatting numbers... 🔢",
                        "Processing completed successfully!": "Almost done! 🎉",
                    }
                    status_text.value = fun_messages.get(msg, msg)
                    page.update()
                
                processed_data = process_customer_list(
                    selected_file_path,
                    status_callback=update_status
                )
                
                # Update UI directly (page.update() is thread-safe)
                update_ui_after_processing()
                
            except Exception as ex:
                show_error(str(ex))
        
        # Run processing in background thread
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()
        
    def update_ui_after_processing():
        nonlocal processed_data
        # Clear existing rows
        data_table.rows = []
        
        # Add only first 5 rows from processed data
        row_number = 1
        for idx, row in processed_data.head(5).iterrows():
            phone = str(row.get('numberr', ''))
            name = str(row.get('name', ''))
            sp = str(row.get('sp', ''))
            products = str(row.get('products', ''))
            
            data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row_number))),
                        ft.DataCell(ft.Text(phone)),
                        ft.DataCell(ft.Text(name)),
                        ft.DataCell(ft.Text(sp)),
                        ft.DataCell(ft.Text(products)),
                    ]
                )
            )
            row_number += 1
        
        # Hide loading spinner and show results
        loading_spinner.visible = False
        scrollable_table.visible = True
        status_text.value = f"All done! 🎉 Processed {len(processed_data)} customers successfully. Ready to export!"
        status_text.color = ft.Colors.GREEN_700
        export_btn.disabled = False
        page.update()
    
    def show_error(error_msg):
        loading_spinner.visible = False
        status_text.value = f"Oops! Something went wrong 😅 Error: {error_msg}"
        status_text.color = ft.Colors.RED_700
        page.update()
    
    def export_file(e):
        nonlocal processed_data, selected_output_path
        
        if processed_data is None:
            status_text.value = "No data to export! Process a file first 😊"
            status_text.color = ft.Colors.RED_700
            page.update()
            return
        
        try:
            # If no output path selected, save next to input file
            if not selected_output_path:
                output_dir = os.path.dirname(selected_file_path) if os.path.dirname(selected_file_path) else '.'
                output_path = os.path.join(output_dir, 'final_merged_list.xlsx')
            else:
                output_path = selected_output_path
            
            processed_data.to_excel(output_path, index=False)
            status_text.value = f"File saved successfully! 🎊 Check it out: {os.path.basename(output_path)}"
            status_text.color = ft.Colors.GREEN_700
            page.update()
        except Exception as ex:
            status_text.value = f"Oops! Couldn't save file 😅 Error: {str(ex)}"
            status_text.color = ft.Colors.RED_700
            page.update()
    
    select_output_btn = ft.ElevatedButton(
        "Choose Output Location",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=select_output_path,
    )
    
    export_btn = ft.ElevatedButton(
        "Save File",
        icon=ft.Icons.DOWNLOAD,
        on_click=export_file,
        disabled=True,
    )
    
    # Layout
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    # Logo
                    ft.Row(
                        controls=[logo_image] if logo_image else [],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ) if logo_image else ft.Container(height=0),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT) if logo_image else ft.Divider(height=0, color=ft.Colors.TRANSPARENT),
                    # App Title
                    ft.Row(
                        controls=[
                            ft.Text("Carno Academy Super RFM", size=28, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                    # Drag and drop area centered
                    ft.Row(
                        controls=[drag_drop_container],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    # Loading spinner
                    ft.Row(
                        controls=[loading_spinner],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    # Status text
                    ft.Row(
                        controls=[status_text],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    # Buttons
                    ft.Row(
                        controls=[
                            select_output_btn,
                            export_btn,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    # Results table
                    ft.Text("Processed Customers:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    scrollable_table,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
    )

if __name__ == "__main__":
    # To set a custom icon, place an icon.ico file in the same directory as this script
    # Icon requirements:
    # - Format: .ico (Windows Icon format)
    # - Recommended sizes: 16x16, 32x32, 48x48, 256x256 pixels (multi-resolution ICO)
    # - You can create ICO files using online tools like:
    #   - https://convertio.co/png-ico/
    #   - https://www.icoconverter.com/
    #   - Or use image editing software like GIMP, Photoshop, etc.
    # - The icon file should be named "icon.ico" and placed in the project root
    ft.app(target=main)

