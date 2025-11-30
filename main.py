import flet as ft
from database import Database
from datetime import datetime


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
        
        # Window drag state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.window_start_x = 0
        self.window_start_y = 0
        
        # Build UI
        self.build_ui()
        
        # Log app start
        self.db.log_action("app_started", {"timestamp": datetime.now().isoformat()})
    
    def setup_page(self):
        """Configure page settings"""
        self.page.title = "Customers List App"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_resizable = True
        self.page.window_min_width = 800
        self.page.window_min_height = 600
        
        # Remove default window controls (we'll create custom ones)
        # Use try-except for compatibility with different Flet versions
        try:
            self.page.window_title_bar_hidden = True
            self.page.window_frameless = True
        except AttributeError:
            # If these properties don't exist, continue without them
            pass
        
        # Set theme
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#F5F5F5"
    
    def build_ui(self):
        """Build the main UI structure"""
        # Custom title bar with window controls
        title_bar = self.create_title_bar()
        
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
                ft.Column(
                    controls=[
                        title_bar,
                        main_layout
                    ],
                    spacing=0,
                    expand=True
                ),
                self.blur_overlay,
                # Popups will be added here dynamically
            ],
            expand=True
        )
        self.page.add(self.main_stack)
    
    def create_title_bar(self):
        """Create custom title bar with window controls"""
        title_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Customers List App",
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color="#333333"
                    ),
                    ft.Container(expand=True),  # Spacer
                    # Minimize button
                    ft.IconButton(
                        icon="remove",
                        icon_size=16,
                        tooltip="Minimize",
                        on_click=self.minimize_window,
                        style=ft.ButtonStyle(
                            color="#666666",
                            overlay_color=color_with_opacity("#000000", 0.1)
                        )
                    ),
                    # Close button
                    ft.IconButton(
                        icon="close",
                        icon_size=16,
                        tooltip="Close",
                        on_click=self.close_window,
                        style=ft.ButtonStyle(
                            color="#666666",
                            overlay_color=color_with_opacity("#FF0000", 0.2)
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=35,
            padding=ft.padding.only(left=15, right=5),
            bgcolor="#FFFFFF",
            border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0"))
        )
        # Enable window dragging on title bar (if supported)
        # Note: Pan events might not be available in all Flet versions
        # We'll set them if the Container supports them
        if hasattr(title_bar, 'on_pan_start'):
            title_bar.on_pan_start = self.on_drag_start
        if hasattr(title_bar, 'on_pan_update'):
            title_bar.on_pan_update = self.on_drag_update
        return title_bar
    
    def on_drag_start(self, e: ft.DragStartEvent):
        """Handle drag start for window movement"""
        try:
            self.drag_start_x = e.global_x
            self.drag_start_y = e.global_y
            self.window_start_x = self.page.window.left if hasattr(self.page.window, 'left') else 0
            self.window_start_y = self.page.window.top if hasattr(self.page.window, 'top') else 0
        except (AttributeError, TypeError):
            pass
    
    def on_drag_update(self, e: ft.DragUpdateEvent):
        """Handle drag update for window movement"""
        try:
            if hasattr(self, 'drag_start_x') and hasattr(self.page.window, 'left'):
                delta_x = e.global_x - self.drag_start_x
                delta_y = e.global_y - self.drag_start_y
                self.page.window.left = self.window_start_x + delta_x
                self.page.window.top = self.window_start_y + delta_y
                self.page.update()
        except (AttributeError, TypeError):
            pass
    
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
        
        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=search_bar,
                        padding=ft.padding.all(20),
                        width=600,
                        alignment=ft.alignment.top_center
                    ),
                    # Main content area (empty for now, can be expanded later)
                    ft.Container(
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
        
        # User profile icon
        profile_icon = ft.IconButton(
            icon="lock",
            icon_size=24,
            tooltip="User Profile",
            on_click=self.on_profile_click,
            style=ft.ButtonStyle(
                color="#666666"
            )
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
    def minimize_window(self, e):
        """Minimize the window"""
        try:
            self.page.window.minimized = True
            self.page.update()
        except (AttributeError, TypeError):
            # If minimize is not supported, just log the action
            pass
        self.db.log_action("window_minimized")
    
    def close_window(self, e):
        """Close the window"""
        self.db.log_action("app_closed", {"timestamp": datetime.now().isoformat()})
        try:
            self.page.window.close()
        except (AttributeError, TypeError):
            # If close is not supported, try alternative
            try:
                import sys
                sys.exit()
            except:
                pass
    
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
        # TODO: Implement upload/download functionality
        print("Upload/Download clicked")
    
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


def main(page: ft.Page):
    app = MainApp(page)


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")

