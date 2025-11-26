"""
Main UI module for Carno Academy Super RFM.
This module handles routing and page navigation.
"""
import flet as ft
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.pages.file_selection_page import create_file_selection_page
from ui.pages.results_page import create_results_page

def main(page: ft.Page):
    page.title = "Carno Academy Super RFM"
    page.window.width = page.window.max_width
    page.window.height = page.window.max_height
    page.window.maximized = True
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Set window icon
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(project_root, "assets")
    icon_path = None
    
    for icon_name in ["myicon.ico", "icon.ico"]:
        test_path = os.path.join(assets_dir, icon_name)
        if os.path.exists(test_path):
            icon_path = test_path
            break
        test_path = os.path.join(project_root, icon_name)
        if os.path.exists(test_path):
            icon_path = test_path
            break
    
    if icon_path:
        try:
            page.window.icon = icon_path
        except Exception as e:
            print(f"Error setting window icon: {e}")
    
    # Store processed data for navigation
    processed_data_store = [None]
    
    def navigate_to_results(processed_data):
        """Navigate to results page"""
        processed_data_store[0] = processed_data
        # Update views and navigate
        page.views.clear()
        page.views.append(
            ft.View(
                route="/results",
                controls=[
                    create_results_page(page, processed_data),
                ],
                padding=0,
            )
        )
        page.route = "/results"
        page.update()
    
    def route_change(route):
        """Handle route changes"""
        page.views.clear()
        
        if page.route == "/results" and processed_data_store[0] is not None:
            page.views.append(
                ft.View(
                    route="/results",
                    controls=[
                        create_results_page(page, processed_data_store[0]),
                    ],
                    padding=0,
                )
            )
        else:
            # Default to file selection page
            page.views.append(
                ft.View(
                    route="/",
                    controls=[
                        create_file_selection_page(page, navigate_to_results),
                    ],
                    padding=20,
                )
            )
        
        page.update()
    
    def view_pop(view):
        """Handle back navigation"""
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Initialize with file selection page
    route_change("/")

if __name__ == "__main__":
    ft.app(target=main)
