import flet as ft
from database import Database
from datetime import datetime
import pandas as pd
import os
from io import BytesIO


def color_with_opacity(color_hex: str, opacity: float) -> str:
    """Convert hex color to rgba string with opacity"""
    # Remove # if present
    color_hex = color_hex.lstrip('#')
    # Convert to RGB
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)
    # Return rgba string
    return f"rgba({r}, {g}, {b}, {opacity})"

class MainApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = Database()
        
        # Setup page
        self.setup_page()
        
        # State for popups
        self.settings_popup_open = False
        self.dashboard_popup_open = False
        self.upload_popup_open = False
        
        # State for Excel data
        self.excel_data = None
        self.excel_df = None
        self.filtered_df = None
        self.column_sort_states = {}  # Track sort state for each column
        self.column_filter_states = {}  # Track filter state for each column (None: all, True: only 1, False: only empty)
        
        # Initialize file picker
        self.file_picker = ft.FilePicker(
            on_result=self.on_file_picked
        )
        self.page.overlay.append(self.file_picker)
        
        # Build UI
        self.build_ui()
        
        # Log app start
        self.db.log_action("app_started", {"timestamp": datetime.now().isoformat()})
    
    def setup_page(self):
        """Configure page settings"""
        self.page.title = "Sheetil"
        # Set window size and properties
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_resizable = True
        self.page.window_min_width = 800
        self.page.window_min_height = 600
        
        # Remove default window title bar (we'll create custom one)
        # This must be set early, before window is displayed
        try:
            self.page.window_title_bar_hidden = True
            self.page.window_frameless = True
        except AttributeError:
            try:
                # Try alternative property names
                if hasattr(self.page, 'window'):
                    if hasattr(self.page.window, 'title_bar_hidden'):
                        self.page.window.title_bar_hidden = True
                    if hasattr(self.page.window, 'frameless'):
                        self.page.window.frameless = True
            except:
                pass
        
        # Center window - must be done after window properties are set
        self.center_window()
        
        # Set theme
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#F5F5F5"
    
    def center_window(self):
        """Center the window on screen"""
        try:
            import tkinter as tk
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            window_left = (screen_width - 1200) // 2
            window_top = (screen_height - 800) // 2
            
            # Set window position - try multiple methods
            try:
                self.page.window.left = window_left
                self.page.window.top = window_top
            except (AttributeError, TypeError):
                try:
                    # Alternative: update window properties
                    if hasattr(self.page.window, 'set_position'):
                        self.page.window.set_position(window_left, window_top)
                except:
                    pass
        except Exception as e:
            # If tkinter is not available, window will open at default position
            pass
    
    def build_ui(self):
        """Build the main UI structure"""
        # Main content area with search
        main_content = self.create_main_content()
        
        # Right sidebar
        sidebar = self.create_sidebar()
        
        # Main layout
        main_layout = ft.Row(
            controls=[
                main_content,
                sidebar
            ],
            expand=True,
            spacing=0
        )
        
        # Container for blur effect (hidden by default)
        # Note: Flet doesn't support CSS blur, so we use a semi-transparent overlay
        self.blur_overlay = ft.Container(
            bgcolor="#000000",
            opacity=0.0,
            expand=True,
            visible=False,
            animate_opacity=300,
            on_click=self.close_all_popups
        )
        
        # Stack to hold everything (for popup overlay)
        self.main_stack = ft.Stack(
            controls=[
                main_layout,
                self.blur_overlay,
                # Popups will be added here dynamically
            ],
            expand=True
        )
        self.page.add(self.main_stack)
    
    def create_main_content(self):
        """Create main content area with search bar"""
        search_bar = ft.TextField(
            hint_text="Search",
            prefix_icon="search",
            border_radius=8,
            bgcolor="#FFFFFF",
            border_color="#E0E0E0",
            focused_border_color="#2196F3",
            content_padding=ft.padding.symmetric(horizontal=15, vertical=12),
            on_submit=self.on_search,
            on_change=self.on_search_change
        )
        
        # Main content area - will be updated when Excel is loaded
        self.main_content_area = ft.Container(
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Main content area",
                        size=16,
                        color="#999999",
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        
        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=search_bar,
                        padding=ft.padding.all(20),
                        width=600,
                        alignment=ft.alignment.top_center
                    ),
                    self.main_content_area
                ],
                spacing=0,
                expand=True
            ),
            expand=True,
            bgcolor="#FFFFFF",
            padding=0
        )
        return main_content
    
    def create_sidebar(self):
        """Create right sidebar with navigation buttons"""
        # Top navigation buttons
        history_btn = ft.ElevatedButton(
            text="History",
            icon="history",
            on_click=self.on_history_click,
            style=ft.ButtonStyle(
                bgcolor="#2196F3",
                color="#FFFFFF",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            width=200
        )
        
        upload_download_btn = ft.ElevatedButton(
            text="Upload/Download",
            icon="file_upload",
            on_click=self.on_upload_download_click,
            style=ft.ButtonStyle(
                bgcolor="#4CAF50",
                color="#FFFFFF",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            width=200
        )
        
        rfm_btn = ft.ElevatedButton(
            text="RFM",
            icon="analytics",
            on_click=self.on_rfm_click,
            style=ft.ButtonStyle(
                bgcolor="#FF9800",
                color="#FFFFFF",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            width=200
        )
        
        crm_btn = ft.ElevatedButton(
            text="CRM",
            icon="people",
            on_click=self.on_crm_click,
            style=ft.ButtonStyle(
                bgcolor="#9C27B0",
                color="#FFFFFF",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            width=200
        )
        
        # Bottom utility buttons
        settings_btn = ft.ElevatedButton(
            text="Settings",
            icon="settings",
            on_click=self.on_settings_click,
            style=ft.ButtonStyle(
                bgcolor="#607D8B",
                color="#FFFFFF",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            width=200
        )
        
        dashboard_btn = ft.ElevatedButton(
            text="Dashboard",
            icon="dashboard",
            on_click=self.on_dashboard_click,
            style=ft.ButtonStyle(
                bgcolor="#795548",
                color="#FFFFFF",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            width=200
        )
        
        # User profile avatar
        profile_icon = ft.Container(
            content=ft.CircleAvatar(
                content=ft.Icon("account_circle", size=24, color="#666666"),
                radius=20,
                bgcolor="#E0E0E0"
            ),
            tooltip="User Profile",
            on_click=self.on_profile_click,
            width=40,
            height=40
        )
        
        sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    # Top navigation
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                history_btn,
                                upload_download_btn,
                                rfm_btn,
                                crm_btn
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=ft.padding.all(20)
                    ),
                    # Spacer
                    ft.Container(expand=True),
                    # Bottom utilities
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                settings_btn,
                                dashboard_btn,
                                ft.Container(height=10),
                                profile_icon
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=ft.padding.all(20)
                    )
                ],
                spacing=0,
                expand=True
            ),
            width=250,
            bgcolor="#F8F8F8",
            border=ft.border.only(left=ft.BorderSide(1, "#E0E0E0"))
        )
        return sidebar
    
    def create_settings_popup(self):
        """Create settings popup"""
        settings_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Settings",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#333333"
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon="close",
                                on_click=self.close_settings_popup,
                                tooltip="Close"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(),
                    ft.Text("Settings content will be added here", size=16, color="#666666"),
                    ft.Text("This is where you can configure app settings", size=14, color="#999999")
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO
            ),
            width=500,
            height=400,
            padding=ft.padding.all(20),
            bgcolor="#FFFFFF",
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=15,
                color=color_with_opacity("#000000", 0.3),
                offset=ft.Offset(0, 5)
            )
        )
        
        return ft.Container(
            content=settings_content,
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
            animate_opacity=300
        )
    
    def create_dashboard_popup(self):
        """Create dashboard popup"""
        # Get recent actions from database
        recent_actions = self.db.get_recent_actions(days=7, limit=10)
        
        action_items = []
        if recent_actions:
            for action in recent_actions:
                action_time = datetime.fromisoformat(action['timestamp']).strftime("%Y-%m-%d %H:%M")
                action_items.append(
                    ft.ListTile(
                        title=ft.Text(action['action_type'], size=14),
                        subtitle=ft.Text(action_time, size=12, color="#999999"),
                        leading=ft.Icon("history", size=20)
                    )
                )
        else:
            action_items.append(
                ft.Text("No recent actions", size=14, color="#999999", text_align=ft.TextAlign.CENTER)
            )
        
        dashboard_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Dashboard",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#333333"
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon="close",
                                on_click=self.close_dashboard_popup,
                                tooltip="Close"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(),
                    ft.Text("Recent Activity", size=18, weight=ft.FontWeight.W_500, color="#333333"),
                    ft.Container(
                        content=ft.Column(
                            controls=action_items,
                            spacing=5,
                            scroll=ft.ScrollMode.AUTO
                        ),
                        height=300,
                        padding=ft.padding.symmetric(vertical=10)
                    )
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO
            ),
            width=600,
            height=500,
            padding=ft.padding.all(20),
            bgcolor="#FFFFFF",
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=15,
                color=color_with_opacity("#000000", 0.3),
                offset=ft.Offset(0, 5)
            )
        )
        
        return ft.Container(
            content=dashboard_content,
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
            animate_opacity=300
        )
    
    # Event handlers
    def on_search(self, e):
        """Handle search submission"""
        query = e.control.value
        if query:
            self.db.save_search(query)
            self.db.log_action("search_performed", {"query": query})
            # TODO: Implement search functionality
            print(f"Searching for: {query}")
    
    def on_search_change(self, e):
        """Handle search text changes"""
        pass
    
    def on_history_click(self, e):
        """Handle history button click"""
        self.db.log_action("history_button_clicked")
        # TODO: Implement history functionality
        print("History clicked")
    
    def on_upload_download_click(self, e):
        """Handle upload/download button click"""
        self.db.log_action("upload_download_button_clicked")
        self.open_upload_popup()
    
    def on_rfm_click(self, e):
        """Handle RFM button click"""
        self.db.log_action("rfm_button_clicked")
        # TODO: Implement RFM functionality
        print("RFM clicked")
    
    def on_crm_click(self, e):
        """Handle CRM button click"""
        self.db.log_action("crm_button_clicked")
        # TODO: Implement CRM functionality
        print("CRM clicked")
    
    def on_settings_click(self, e):
        """Handle settings button click"""
        self.db.log_action("settings_button_clicked")
        self.open_settings_popup()
    
    def on_dashboard_click(self, e):
        """Handle dashboard button click"""
        self.db.log_action("dashboard_button_clicked")
        self.open_dashboard_popup()
    
    def on_profile_click(self, e):
        """Handle profile icon click"""
        self.db.log_action("profile_icon_clicked")
        # TODO: Implement profile functionality
        print("Profile clicked")
    
    def open_settings_popup(self):
        """Open settings popup"""
        if not self.settings_popup_open:
            self.settings_popup_open = True
            self.blur_overlay.visible = True
            self.blur_overlay.opacity = 0.5
            
            # Create and add settings popup if not exists
            if not hasattr(self, 'settings_popup'):
                self.settings_popup = self.create_settings_popup()
                self.main_stack.controls.append(self.settings_popup)
            
            self.settings_popup.visible = True
            self.page.update()
    
    def close_settings_popup(self, e=None):
        """Close settings popup"""
        if self.settings_popup_open:
            self.settings_popup_open = False
            if hasattr(self, 'settings_popup'):
                self.settings_popup.visible = False
            self.blur_overlay.opacity = 0.0
            self.blur_overlay.visible = False
            self.page.update()
    
    def open_dashboard_popup(self):
        """Open dashboard popup"""
        if not self.dashboard_popup_open:
            self.dashboard_popup_open = True
            self.blur_overlay.visible = True
            self.blur_overlay.opacity = 0.5
            
            # Recreate dashboard popup to get fresh data
            if hasattr(self, 'dashboard_popup'):
                if self.dashboard_popup in self.main_stack.controls:
                    self.main_stack.controls.remove(self.dashboard_popup)
            
            self.dashboard_popup = self.create_dashboard_popup()
            self.main_stack.controls.append(self.dashboard_popup)
            self.dashboard_popup.visible = True
            self.page.update()
    
    def close_dashboard_popup(self, e=None):
        """Close dashboard popup"""
        if self.dashboard_popup_open:
            self.dashboard_popup_open = False
            if hasattr(self, 'dashboard_popup'):
                self.dashboard_popup.visible = False
            self.blur_overlay.opacity = 0.0
            self.blur_overlay.visible = False
            self.page.update()
    
    def close_all_popups(self, e):
        """Close all open popups"""
        self.close_settings_popup()
        self.close_dashboard_popup()
        self.close_upload_popup()
    
    def create_upload_popup(self):
        """Create upload/download popup with drag and drop"""
        # Drag and drop area
        drag_drop_area = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon("cloud_upload", size=48, color="#2196F3"),
                    ft.Text(
                        "Click to select Excel file",
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color="#666666"
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            expand=True,
            height=200,
            border=ft.border.all(2, "#E0E0E0"),
            border_radius=10,
            bgcolor="#F8F8F8",
            padding=ft.padding.all(20),
            alignment=ft.alignment.center,
            on_click=self.browse_files
        )
        
        upload_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Upload Excel File",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#333333"
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon="close",
                                on_click=self.close_upload_popup,
                                tooltip="Close"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(),
                    drag_drop_area,
                    ft.Text(
                        "Supported format: .xlsx",
                        size=12,
                        color="#999999",
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO
            ),
            width=600,
            height=400,
            padding=ft.padding.all(20),
            bgcolor="#FFFFFF",
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=15,
                color=color_with_opacity("#000000", 0.3),
                offset=ft.Offset(0, 5)
            )
        )
        
        return ft.Container(
            content=upload_content,
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
            animate_opacity=300
        )
    
    def browse_files(self, e):
        """Open file picker dialog"""
        try:
            if self.file_picker:
                self.file_picker.pick_files(
                    allowed_extensions=["xlsx"],
                    dialog_title="Select Excel File"
                )
                self.page.update()
            else:
                # Re-initialize if not set
                self.file_picker = ft.FilePicker(
                    on_result=self.on_file_picked
                )
                self.page.overlay.append(self.file_picker)
                self.file_picker.pick_files(
                    allowed_extensions=["xlsx"],
                    dialog_title="Select Excel File"
                )
                self.page.update()
        except Exception as ex:
            print(f"Error opening file picker: {ex}")
    
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            self.load_excel_file(file_path)
    
    def load_excel_file(self, file_path: str):
        """Load Excel file and display in table"""
        try:
            # Show loading indicator
            self.show_loading_indicator()
            self.page.update()
            
            # Read Excel file
            self.excel_df = pd.read_excel(file_path)
            self.filtered_df = self.excel_df.copy()
            
            # Log action
            self.db.log_action("excel_file_uploaded", {"file_path": file_path, "rows": len(self.excel_df), "columns": len(self.excel_df.columns)})
            
            # Close upload popup
            self.close_upload_popup()
            
            # Hide loading indicator
            self.hide_loading_indicator()
            
            # Display table in main content
            self.display_excel_table()
            
        except Exception as e:
            # Hide loading indicator on error
            self.hide_loading_indicator()
            # Show error message
            self.show_error_message(f"Error loading file: {str(e)}")
    
    def display_excel_table(self):
        """Display Excel data in a table with filters and sorting"""
        if self.excel_df is None or len(self.excel_df) == 0:
            return
        
        # Calculate unique values in first column
        first_col = self.excel_df.columns[0]
        unique_count = self.excel_df[first_col].nunique()
        
        # Calculate count of "1" values in each column
        column_one_counts = {}
        for col in self.excel_df.columns:
            # Count values that are exactly "1" or 1
            count = 0
            for val in self.excel_df[col]:
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str == "1" or val_str == "1.0":
                        count += 1
            column_one_counts[col] = count
        
        # Create filter controls for each column (three-state switches)
        filter_controls = []
        
        for col in self.excel_df.columns:
            filter_switch = self.create_three_state_filter(col)
            filter_controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(col, size=12, weight=ft.FontWeight.W_500),
                            filter_switch
                        ],
                        spacing=5,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=ft.padding.all(5)
                )
            )
        
        # Determine which columns to show (hide columns with filter state 0 or 1)
        visible_columns = []
        for col in self.excel_df.columns:
            filter_state = self.column_filter_states.get(col, None)
            # Show column only if filter is None (all values)
            if filter_state is None:
                visible_columns.append(col)
        
        # Create data table with only visible columns
        data_rows = []
        for idx, row in self.filtered_df.iterrows():
            cells = [ft.DataCell(ft.Text(str(row[col])[:50] if pd.notna(row[col]) else "")) for col in visible_columns]
            data_rows.append(ft.DataRow(cells=cells))
        
        # Create sortable column headers with count of "1" values (only for visible columns)
        column_headers = []
        for col in visible_columns:
            sort_btn = ft.IconButton(
                icon="sort",
                icon_size=16,
                tooltip=f"Sort {col}",
                on_click=lambda e, col=col: self.sort_column(e, col)
            )
            one_count = column_one_counts.get(col, 0)
            column_headers.append(
                ft.DataColumn(
                    label=ft.Row(
                        controls=[
                            ft.Text(col, size=12, weight=ft.FontWeight.W_500),
                            ft.Text(f"({one_count})", size=10, color="#666666"),
                            sort_btn
                        ],
                        spacing=5
                    )
                )
            )
        
        data_table = ft.DataTable(
            columns=column_headers,
            rows=data_rows[:1000],  # Limit to 1000 rows for performance
            heading_row_color="#E0E0E0",
            heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            data_row_max_height=50,
            border=ft.border.all(1, "#E0E0E0"),
            border_radius=5
        )
        
        # Create scrollable table container
        table_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"تعداد ردیف‌های با شماره یکتا: {unique_count}",
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color="#2196F3"
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                f"نمایش {len(self.filtered_df)} ردیف",
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color="#666666"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(
                                    content=ft.Row(
                                        controls=[data_table],
                                        scroll=ft.ScrollMode.AUTO
                                    ),
                                    padding=ft.padding.all(10),
                                    expand=True
                                )
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            expand=True
                        ),
                        expand=True,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    )
                ],
                spacing=10,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            expand=True,
            border=ft.border.all(1, "#E0E0E0"),
            border_radius=5,
            bgcolor="#FFFFFF"
        )
        
        # Update main content area
        self.main_content_area.content = ft.Column(
            controls=[
                ft.Row(
                    controls=filter_controls,
                    wrap=True,
                    scroll=ft.ScrollMode.AUTO
                ),
                ft.Container(
                    content=table_container,
                    expand=True,
                    padding=ft.padding.all(10)
                )
            ],
            spacing=10,
            expand=True
        )
        
        self.page.update()
    
    def apply_column_filter(self, column: str, filter_value: str):
        """Apply filter to a specific column"""
        if self.excel_df is None:
            return
        
        if not filter_value or filter_value.strip() == "":
            self.filtered_df = self.excel_df.copy()
        else:
            try:
                # Try numeric filter
                if self.excel_df[column].dtype in ['int64', 'float64']:
                    filter_value_num = float(filter_value)
                    self.filtered_df = self.excel_df[self.excel_df[column] == filter_value_num]
                else:
                    # Text filter
                    self.filtered_df = self.excel_df[
                        self.excel_df[column].astype(str).str.contains(filter_value, case=False, na=False)
                    ]
            except:
                # Fallback to text filter
                self.filtered_df = self.excel_df[
                    self.excel_df[column].astype(str).str.contains(filter_value, case=False, na=False)
                ]
        
        # Refresh table display
        self.display_excel_table()
    
    def sort_column(self, e, column: str):
        """Sort table by column"""
        if self.filtered_df is None:
            return
        
        # Toggle ascending/descending
        if column in self.column_sort_states:
            ascending = not self.column_sort_states[column]
        else:
            ascending = True
        
        self.column_sort_states[column] = ascending
        self.filtered_df = self.filtered_df.sort_values(by=column, ascending=ascending)
        
        # Refresh table display
        self.display_excel_table()
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        # Simple error display - can be improved with a proper dialog
        print(f"Error: {message}")
    
    def show_loading_indicator(self):
        """Show loading indicator in main content area"""
        self.main_content_area.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.ProgressRing(width=50, height=50, stroke_width=3),
                            ft.Text(
                                "در حال پردازش فایل اکسل... لطفاً صبر کنید",
                                size=16,
                                weight=ft.FontWeight.W_500,
                                color="#666666"
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    
    def hide_loading_indicator(self):
        """Hide loading indicator"""
        # The indicator will be replaced when display_excel_table is called
        pass
    
    def create_three_state_filter(self, column: str):
        """Create a three-state filter switch for a column"""
        # Initialize filter state if not exists
        if column not in self.column_filter_states:
            self.column_filter_states[column] = None  # None = all, True = only 1, False = only empty
        
        current_state = self.column_filter_states[column]
        
        # Create three buttons for the three states
        left_btn = ft.IconButton(
            icon="radio_button_unchecked" if current_state != False else "radio_button_checked",
            icon_color="#666666" if current_state != False else "#2196F3",
            tooltip="فقط مقادیر خالی",
            on_click=lambda e, col=column: self.set_filter_state(col, False)
        )
        
        middle_btn = ft.IconButton(
            icon="radio_button_unchecked" if current_state != None else "radio_button_checked",
            icon_color="#666666" if current_state != None else "#2196F3",
            tooltip="همه مقادیر",
            on_click=lambda e, col=column: self.set_filter_state(col, None)
        )
        
        right_btn = ft.IconButton(
            icon="radio_button_unchecked" if current_state != True else "radio_button_checked",
            icon_color="#666666" if current_state != True else "#2196F3",
            tooltip="فقط مقادیر 1",
            on_click=lambda e, col=column: self.set_filter_state(col, True)
        )
        
        return ft.Row(
            controls=[left_btn, middle_btn, right_btn],
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER
        )
    
    def set_filter_state(self, column: str, state):
        """Set filter state for a column and apply filters"""
        self.column_filter_states[column] = state
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all column filters"""
        if self.excel_df is None:
            return
        
        self.filtered_df = self.excel_df.copy()
        
        # Apply each column filter
        for col, state in self.column_filter_states.items():
            if state is None:
                # Show all values - no filtering
                continue
            elif state is True:
                # Show only "1" values
                mask = self.filtered_df[col].apply(
                    lambda x: pd.notna(x) and (str(x).strip() == "1" or str(x).strip() == "1.0")
                )
                self.filtered_df = self.filtered_df[mask]
            elif state is False:
                # Show only empty values
                mask = self.filtered_df[col].isna() | (self.filtered_df[col].astype(str).str.strip() == "")
                self.filtered_df = self.filtered_df[mask]
        
        # Refresh table display
        self.display_excel_table()
    
    def open_upload_popup(self):
        """Open upload popup"""
        if not self.upload_popup_open:
            self.upload_popup_open = True
            self.blur_overlay.visible = True
            self.blur_overlay.opacity = 0.5
            
            # Create and add upload popup if not exists
            if not hasattr(self, 'upload_popup'):
                self.upload_popup = self.create_upload_popup()
                self.main_stack.controls.append(self.upload_popup)
            
            self.upload_popup.visible = True
            self.page.update()
    
    def close_upload_popup(self, e=None):
        """Close upload popup"""
        if self.upload_popup_open:
            self.upload_popup_open = False
            if hasattr(self, 'upload_popup'):
                self.upload_popup.visible = False
            self.blur_overlay.opacity = 0.0
            self.blur_overlay.visible = False
            self.page.update()


def main(page: ft.Page):
    app = MainApp(page)


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")

