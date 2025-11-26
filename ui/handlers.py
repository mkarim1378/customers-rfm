"""
UI Event Handlers module.
Contains all event handler functions for UI interactions.
"""
import os
import sys
import threading
import flet as ft

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing.data_processing import process_customer_list

def create_file_selection_handler(selected_file_path_ref, file_info_ref, drag_drop_content, 
                                  status_text, loading_spinner, start_processing_func, 
                                  get_file_size_func, update_file_upload_container_func):
    """Create file selection handler"""
    def handle_file_selection(file_path):
        selected_file_path_ref[0] = file_path
        file_name = os.path.basename(file_path)
        file_size = get_file_size_func(file_path)
        
        # Update drag drop container to show file info
        update_file_upload_container_func(drag_drop_content, file_name, file_size)
        
        status_text.value = "Great! Processing your file now... ⚡"
        status_text.color = ft.Colors.BLUE_700
        
        # Show loading spinner and start processing
        loading_spinner.visible = True
        status_text.page.update()
        
        # Auto-start processing
        start_processing_func()
    
    return handle_file_selection

def create_processing_handler(selected_file_path_ref, processed_data_ref, status_text, 
                              loading_spinner, data_table, scrollable_table, export_btn,
                              update_status_messages):
    """Create file processing handler"""
    def start_processing():
        if not selected_file_path_ref[0]:
            return
        
        def process_in_thread():
            try:
                def update_status(msg):
                    fun_msg = update_status_messages.get(msg, msg)
                    status_text.value = fun_msg
                    status_text.page.update()
                
                processed_data_ref[0] = process_customer_list(
                    selected_file_path_ref[0],
                    status_callback=update_status
                )
                
                # Update UI directly (page.update() is thread-safe)
                update_ui_after_processing()
                
            except Exception as ex:
                show_error(str(ex))
        
        def update_ui_after_processing():
            # Clear existing rows
            data_table.rows = []
            
            # Add only first 5 rows from processed data
            row_number = 1
            for idx, row in processed_data_ref[0].head(5).iterrows():
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
            status_text.value = f"All done! 🎉 Processed {len(processed_data_ref[0])} customers successfully. Ready to export!"
            status_text.color = ft.Colors.GREEN_700
            export_btn.disabled = False
            status_text.page.update()
        
        def show_error(error_msg):
            loading_spinner.visible = False
            status_text.value = f"Oops! Something went wrong 😅 Error: {error_msg}"
            status_text.color = ft.Colors.RED_700
            status_text.page.update()
        
        # Run processing in background thread
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()
    
    return start_processing

def create_export_handler(processed_data_ref, selected_output_path_ref, selected_file_path_ref, 
                          status_text):
    """Create file export handler"""
    def export_file(e):
        if processed_data_ref[0] is None:
            status_text.value = "No data to export! Process a file first 😊"
            status_text.color = ft.Colors.RED_700
            status_text.page.update()
            return
        
        try:
            # If no output path selected, save next to input file
            if not selected_output_path_ref[0]:
                output_dir = os.path.dirname(selected_file_path_ref[0]) if os.path.dirname(selected_file_path_ref[0]) else '.'
                output_path = os.path.join(output_dir, 'final_merged_list.xlsx')
            else:
                output_path = selected_output_path_ref[0]
            
            processed_data_ref[0].to_excel(output_path, index=False)
            status_text.value = f"File saved successfully! 🎊 Check it out: {os.path.basename(output_path)}"
            status_text.color = ft.Colors.GREEN_700
            status_text.page.update()
        except Exception as ex:
            status_text.value = f"Oops! Couldn't save file 😅 Error: {str(ex)}"
            status_text.color = ft.Colors.RED_700
            status_text.page.update()
    
    return export_file

def create_file_picker_handlers(file_picker, handle_file_selection_func):
    """Create file picker handlers"""
    def file_picked(e):
        if e.files and len(e.files) > 0:
            handle_file_selection_func(e.files[0].path)
    
    def select_file(e):
        file_picker.pick_files(
            dialog_title="Select Excel file",
            allowed_extensions=["xlsx", "xls"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
    
    file_picker.on_result = file_picked
    return select_file

def create_output_path_handler(selected_output_path_ref, status_text):
    """Create output path selection handler"""
    def output_path_selected(e):
        if e.path:
            selected_output_path_ref[0] = e.path
            status_text.value = f"Output path set! Ready to export 🎯"
            status_text.color = ft.Colors.GREEN_700
            status_text.page.update()
    
    def select_output_path(e):
        return output_path_selected
    
    return output_path_selected, select_output_path

# Status message mappings for fun messages
STATUS_MESSAGES = {
    "Reading Excel file...": "Reading your file... 📖",
    "Cleaning and standardizing phone numbers...": "Cleaning up phone numbers... 🧹",
    "Normalizing product columns...": "Organizing products... 📦",
    "Merging duplicate records...": "Merging duplicates... 🔄",
    "Updating 'hichi' column...": "Finalizing data... ✨",
    "Building products list...": "Building product list... 🏗️",
    "Formatting phone numbers...": "Formatting numbers... 🔢",
    "Processing completed successfully!": "Almost done! 🎉",
}

