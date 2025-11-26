"""
File selection page - First page where user selects and processes the file.
"""
import flet as ft
import os
import sys
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.data_processing import process_customer_list
from ui.components import (
    create_file_upload_container,
    create_logo_image,
    create_loading_spinner,
    create_status_text,
    get_file_size,
    update_file_upload_container,
)
from ui.handlers import STATUS_MESSAGES

def create_file_selection_page(page: ft.Page, navigate_to_results):
    """Create the file selection page"""
    
    # State variables
    selected_file_path = None
    processed_data = None
    
    # UI Components
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    
    # Create UI components
    loading_spinner = create_loading_spinner()
    status_text = create_status_text()
    
    # Get logo path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_dir = os.path.join(project_root, "assets")
    logo_path = None
    
    for icon_name in ["myicon.ico", "icon.ico"]:
        test_path = os.path.join(assets_dir, icon_name)
        if os.path.exists(test_path):
            logo_path = test_path
            break
        test_path = os.path.join(project_root, icon_name)
        if os.path.exists(test_path):
            logo_path = test_path
            break
    
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
                
                # Navigate to results page after processing
                # Call directly - Flet handles thread safety for page operations
                navigate_to_results(processed_data)
                
            except Exception as ex:
                show_error(str(ex))
        
        def show_error(error_msg):
            loading_spinner.visible = False
            status_text.value = f"Oops! Something went wrong 😅 Error: {error_msg}"
            status_text.color = ft.Colors.RED_700
            page.update()
        
        # Run processing in background thread
        thread = threading.Thread(target=process_in_thread, daemon=True)
        thread.start()
    
    # Create logo
    logo_image = create_logo_image(logo_path)
    
    # Return the page content
    return ft.Container(
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
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )

