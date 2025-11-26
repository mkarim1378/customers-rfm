"""
UI Components module.
Contains all reusable UI components for the application.
"""
import flet as ft
import os
import base64
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def create_file_upload_container(on_click_callback, on_hover_callback=None):
    """Create the file upload container component"""
    container = ft.Container(
        width=500,
        height=300,
        border=ft.border.all(2, ft.Colors.GREY_400),
        border_radius=10,
        bgcolor=ft.Colors.GREY_50,
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.CLOUD_UPLOAD, size=64, color=ft.Colors.BLUE_400),
                ft.Text("Click to select your Excel file", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                ft.Text("Select .xlsx or .xls file", size=14, color=ft.Colors.GREY_600),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        ),
        on_click=on_click_callback,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )
    
    if on_hover_callback:
        container.on_hover = on_hover_callback
    
    return container

def create_logo_image(logo_path):
    """Create logo image component from file path"""
    if not logo_path:
        return None
    
    try:
        abs_logo_path = os.path.abspath(logo_path)
        # If it's an ICO file, convert it to base64 for display
        if abs_logo_path.lower().endswith('.ico') and PIL_AVAILABLE:
            # Open ICO file and convert to PNG bytes
            img = Image.open(abs_logo_path)
            # Resize to a reasonable size for display
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            # Convert to base64
            import io
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode()
            return ft.Image(
                src_base64=img_base64,
                width=120,
                height=120,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            # For other formats or if PIL not available, use direct path
            return ft.Image(
                src=abs_logo_path,
                width=120,
                height=120,
                fit=ft.ImageFit.CONTAIN,
            )
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None

def create_data_table():
    """Create the data table component for displaying processed customers"""
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#")),
            ft.DataColumn(ft.Text("Phone")),
            ft.DataColumn(ft.Text("Name")),
            ft.DataColumn(ft.Text("Sales Expert")),
            ft.DataColumn(ft.Text("Products")),
        ],
        rows=[],
    )

def create_loading_spinner():
    """Create loading spinner component"""
    return ft.ProgressRing(
        width=80,
        height=80,
        stroke_width=4,
        visible=False,
    )

def create_status_text():
    """Create status text component"""
    return ft.Text("Ready to process! 🚀", size=16, color=ft.Colors.BLUE_700, weight=ft.FontWeight.W_500)

def create_action_buttons(select_output_callback, export_callback):
    """Create action buttons (Select Output, Export)"""
    select_output_btn = ft.ElevatedButton(
        "Choose Output Location",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=select_output_callback,
    )
    
    export_btn = ft.ElevatedButton(
        "Save File",
        icon=ft.Icons.DOWNLOAD,
        on_click=export_callback,
        disabled=True,
    )
    
    return select_output_btn, export_btn

def get_file_size(file_path):
    """Get file size in human readable format"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def update_file_upload_container(container, file_name, file_size):
    """Update file upload container to show file info"""
    container.content.controls = [
        ft.Icon(ft.Icons.CHECK_CIRCLE, size=64, color=ft.Colors.GREEN_500),
        ft.Text(f"File loaded! ✨", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
        ft.Text(f"{file_name}", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
        ft.Text(f"Size: {file_size}", size=12, color=ft.Colors.GREY_600),
    ]
    container.border = ft.border.all(2, ft.Colors.GREEN_400)
    container.bgcolor = ft.Colors.GREEN_50

