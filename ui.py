"""
Main UI module for Carno Academy Super RFM.
This module orchestrates the UI components and handlers.
"""
import flet as ft
import os
import threading
from data_processing import process_customer_list
from ui_components import (
    create_file_upload_container,
    create_logo_image,
    create_data_table,
    create_loading_spinner,
    create_status_text,
    create_action_buttons,
    get_file_size,
    update_file_upload_container,
)
from ui_handlers import STATUS_MESSAGES

def main(page: ft.Page):
    page.title = "Carno Academy Super RFM"
    page.window.width = page.window.max_width
    page.window.height = page.window.max_height
    page.window.maximized = True
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Set window icon and logo (simple approach)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = None
    logo_path = None
    
    # Try myicon.ico first, then icon.ico
    for icon_name in ["myicon.ico", "icon.ico"]:
        test_path = os.path.join(base_dir, icon_name)
        if os.path.exists(test_path):
            icon_path = test_path
            logo_path = test_path
            break
    
    # Set window icon
    if icon_path:
        try:
            page.window.icon = icon_path
        except Exception as e:
            print(f"Error setting window icon: {e}")
    
    # State variables
    selected_file_path = None
    selected_output_path = None
    processed_data = None
    
    # UI Components
    file_picker = ft.FilePicker()
    save_file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    page.overlay.append(save_file_picker)
    
    # Create UI components
    loading_spinner = create_loading_spinner()
    status_text = create_status_text()
    data_table = create_data_table()
    
    scrollable_table = ft.Container(
        content=ft.Column(
            controls=[data_table],
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        visible=False,
    )
    
    # Create file upload container with hover handler
    def on_hover_drag_box(e):
        if e.data == "true":
            drag_drop_content.border = ft.border.all(3, ft.Colors.BLUE_400)
            drag_drop_content.bgcolor = ft.Colors.BLUE_50
        else:
            if selected_file_path is None:
                drag_drop_content.border = ft.border.all(2, ft.Colors.GREY_400)
                drag_drop_content.bgcolor = ft.Colors.GREY_50
        page.update()
    
    def select_file(e):
        file_picker.pick_files(
            dialog_title="Select Excel file",
            allowed_extensions=["xlsx", "xls"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
    
    # Create file upload container
    drag_drop_content = create_file_upload_container(select_file, on_hover_drag_box)
    drag_drop_container = drag_drop_content
    
    def handle_file_selection(file_path):
        nonlocal selected_file_path
        selected_file_path = file_path
        file_name = os.path.basename(file_path)
        file_size = get_file_size(file_path)
        
        # Update drag drop container to show file info
        update_file_upload_container(drag_drop_content, file_name, file_size)
        
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
    
    file_picker.on_result = file_picked
    
    def output_path_selected(e):
        nonlocal selected_output_path
        if e.path:
            selected_output_path = e.path
            status_text.value = f"Output path set! Ready to export 🎯"
            status_text.color = ft.Colors.GREEN_700
            page.update()
    
    save_file_picker.on_result = output_path_selected
    
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
                    fun_msg = STATUS_MESSAGES.get(msg, msg)
                    status_text.value = fun_msg
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
        
        # Run processing in background thread
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()
    
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
    
    # Create action buttons
    select_output_btn, export_btn = create_action_buttons(select_output_path, export_file)
    
    # Create logo
    logo_image = create_logo_image(logo_path)
    
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
                    # File upload area centered
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
    ft.app(target=main)
