"""
Results page - Displays processed data with sidebar, top bar, and paginated table.
"""
import flet as ft
import pandas as pd

def create_results_page(page: ft.Page, processed_data: pd.DataFrame):
    """Create the results page with sidebar, top bar, and paginated table"""
    
    # Pagination state
    current_page = [1]
    rows_per_page = [30]
    
    # Create data table
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
    
    # Pagination info (must be defined before update_table)
    pagination_info = ft.Text("", size=12, color=ft.Colors.GREY_600)
    
    def update_table():
        """Update table based on current page and rows per page"""
        data_table.rows = []
        
        start_idx = (current_page[0] - 1) * rows_per_page[0]
        end_idx = start_idx + rows_per_page[0]
        
        total_rows = len(processed_data)
        page_data = processed_data.iloc[start_idx:end_idx]
        
        row_number = start_idx + 1
        for idx, row in page_data.iterrows():
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
        
        # Update pagination info
        total_pages = (total_rows + rows_per_page[0] - 1) // rows_per_page[0]
        pagination_info.value = f"Page {current_page[0]} of {total_pages} | Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} rows"
        page.update()
    
    def go_to_page(page_num):
        total_pages = (len(processed_data) + rows_per_page[0] - 1) // rows_per_page[0]
        if 1 <= page_num <= total_pages:
            current_page[0] = page_num
            update_table()
    
    def change_rows_per_page(new_value):
        rows_per_page[0] = int(new_value)
        current_page[0] = 1  # Reset to first page
        update_table()
    
    # Sidebar (placeholder for future features)
    sidebar = ft.Container(
        width=250,
        bgcolor=ft.Colors.GREY_100,
        content=ft.Column(
            controls=[
                ft.Text("Filters", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Sidebar content", size=14, color=ft.Colors.GREY_600),
                ft.Text("(To be implemented)", size=12, color=ft.Colors.GREY_500, italic=True),
            ],
            spacing=10,
            padding=15,
        ),
    )
    
    # Top bar
    top_bar = ft.Container(
        height=60,
        bgcolor=ft.Colors.BLUE_50,
        content=ft.Row(
            controls=[
                ft.Text("Processed Customers", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),  # Spacer
                ft.Text(f"Total: {len(processed_data)} customers", size=14, color=ft.Colors.GREY_700),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            padding=15,
        ),
    )
    
    # Pagination controls
    rows_per_page_dropdown = ft.Dropdown(
        width=100,
        options=[
            ft.dropdown.Option("10"),
            ft.dropdown.Option("20"),
            ft.dropdown.Option("30"),
            ft.dropdown.Option("50"),
            ft.dropdown.Option("100"),
        ],
        value="30",
        on_change=lambda e: change_rows_per_page(e.control.value),
    )
    
    def prev_page(e):
        if current_page[0] > 1:
            go_to_page(current_page[0] - 1)
    
    def next_page(e):
        total_pages = (len(processed_data) + rows_per_page[0] - 1) // rows_per_page[0]
        if current_page[0] < total_pages:
            go_to_page(current_page[0] + 1)
    
    pagination_controls = ft.Row(
        controls=[
            ft.Text("Rows per page:", size=12),
            rows_per_page_dropdown,
            ft.Container(width=20),  # Spacer
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=prev_page,
                tooltip="Previous page",
            ),
            pagination_info,
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                on_click=next_page,
                tooltip="Next page",
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Main content area with table
    main_content = ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Container(
                    content=data_table,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                ),
                ft.Divider(height=10),
                pagination_controls,
            ],
            spacing=10,
            expand=True,
        ),
        padding=15,
    )
    
    # Initial table update
    update_table()
    
    # Main layout with sidebar and content
    return ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1),
            ft.Container(
                expand=True,
                content=ft.Column(
                    controls=[
                        top_bar,
                        main_content,
                    ],
                    spacing=0,
                    expand=True,
                ),
            ),
        ],
        spacing=0,
        expand=True,
    )

