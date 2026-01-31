#!/usr/bin/env python3
"""
Generate the Criticality Analysis Request Form (xlsx) with embedded geometry images.
Run this script to create/update the form.
"""

from pathlib import Path
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


# Base path for the project
BASE_PATH = Path(__file__).parent.parent

# Image mappings: template -> (2D geometry path, 3D voxel path)
IMAGE_PATHS = {
    "single_cylinder": (
        BASE_PATH / "experiments/cascade_lines/_validation/geometry.png",
        BASE_PATH / "experiments/cascade_lines/_validation/voxel_3d.png",
    ),
    "uf6_cylinder": (
        BASE_PATH / "experiments/benchmarks/uf6_30b/_validation/geometry.png",
        BASE_PATH / "experiments/benchmarks/uf6_30b/_validation/voxel_3d.png",
    ),
    "rectangular_box": (
        BASE_PATH / "experiments/rectangular_boxes/_config/_validation/geometry.png",
        BASE_PATH / "experiments/rectangular_boxes/_validation/voxel_3d.png",
    ),
    "cylinder_array": (
        BASE_PATH / "experiments/cylinder_arrays/_validation/geometry.png",
        BASE_PATH / "experiments/cylinder_arrays/_validation/voxel_3d.png",
    ),
    "cylinder_array_3d": (
        BASE_PATH / "experiments/stacked_cylinders/_validation/geometry.png",
        BASE_PATH / "experiments/stacked_cylinders/_validation/voxel_3d.png",
    ),
}


def create_form():
    wb = Workbook()

    # Define styles
    header_font = Font(bold=True, size=14)
    subheader_font = Font(bold=True, size=11)
    bold_font = Font(bold=True)
    wrap_alignment = Alignment(wrap_text=True, vertical='top')
    center_alignment = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font_white = Font(bold=True, color='FFFFFF')
    light_blue_fill = PatternFill(start_color='D6DCE4', end_color='D6DCE4', fill_type='solid')
    light_green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
    light_yellow_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')

    # =========================================================================
    # TAB 1: Instructions
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Instructions"

    ws1['A1'] = "CRITICALITY SAFETY ANALYSIS REQUEST FORM"
    ws1['A1'].font = Font(bold=True, size=18)
    ws1.merge_cells('A1:F1')

    ws1['A3'] = "Purpose"
    ws1['A3'].font = header_font
    ws1['A4'] = ("This form collects the information needed to run parametric criticality safety analyses "
                 "using Monte Carlo simulation (OpenMC). Fill out the Request Form tab with your equipment "
                 "specifications and we'll generate k-effective results for your scenarios.")
    ws1['A4'].alignment = wrap_alignment
    ws1.merge_cells('A4:F4')
    ws1.row_dimensions[4].height = 45

    ws1['A6'] = "How to Use This Form"
    ws1['A6'].font = header_font

    instructions = [
        ("1.", "Review the Application Catalog tab to see available problem types and their geometry visualizations"),
        ("2.", "Check the Reference tabs for available cylinder types and materials"),
        ("3.", "Fill out the Request Form tab - one row per analysis case"),
        ("4.", "For parameter sweeps, specify ranges in the format: min, max, step (e.g., '5, 20, 5' for 5, 10, 15, 20)"),
        ("5.", "Return the completed form to the Criticality Safety team"),
    ]

    for i, (num, text) in enumerate(instructions, start=7):
        ws1[f'A{i}'] = num
        ws1[f'A{i}'].font = bold_font
        ws1[f'B{i}'] = text
        ws1.merge_cells(f'B{i}:F{i}')

    ws1['A13'] = "What We Default (if not specified)"
    ws1['A13'].font = header_font

    defaults = [
        ("UF6 Density", "5.09 g/cc", "Solid UF6 - conservative assumption"),
        ("Reflector", "Water, 30 cm", "Full water reflection - most reactive"),
        ("Wall Material", "Per application", "Steel for process equipment, Monel for 5A/5B cylinders"),
        ("Simulation", "10,000 particles × 150 batches", "Standard convergence settings"),
    ]

    ws1['A14'] = "Parameter"
    ws1['B14'] = "Default Value"
    ws1['C14'] = "Rationale"
    for cell in ['A14', 'B14', 'C14']:
        ws1[cell].font = bold_font
        ws1[cell].fill = light_blue_fill

    for i, (param, value, rationale) in enumerate(defaults, start=15):
        ws1[f'A{i}'] = param
        ws1[f'B{i}'] = value
        ws1[f'C{i}'] = rationale

    ws1['A21'] = "Contact"
    ws1['A21'].font = header_font
    ws1['A22'] = "Questions? Contact the Criticality Safety team."

    # Set column widths
    ws1.column_dimensions['A'].width = 18
    ws1.column_dimensions['B'].width = 20
    ws1.column_dimensions['C'].width = 45
    ws1.column_dimensions['D'].width = 15
    ws1.column_dimensions['E'].width = 15
    ws1.column_dimensions['F'].width = 15

    # =========================================================================
    # TAB 2: Application Catalog
    # =========================================================================
    ws2 = wb.create_sheet("Application Catalog")

    ws2['A1'] = "APPLICATION CATALOG"
    ws2['A1'].font = Font(bold=True, size=18)
    ws2.merge_cells('A1:H1')

    ws2['A3'] = "Available Problem Types"
    ws2['A3'].font = header_font
    ws2['A4'] = "Review the geometry visualizations below to understand what each problem type models."
    ws2.merge_cells('A4:H4')

    # Set column widths for catalog
    for col in range(1, 9):
        ws2.column_dimensions[get_column_letter(col)].width = 18

    # Application entries with embedded images
    row = 6

    applications = [
        {
            "name": "Single Cylinder",
            "template": "single_cylinder",
            "applications": "Process piping, cold traps, RUTS traps, pump cavities, cylindrical GEVS",
            "geometry": "Vertical cylinder with wall and reflector",
            "key_params": "radius_cm, height_cm, wall_thickness_cm",
            "image_height": 280,  # pixels for scaling
        },
        {
            "name": "Shipping Cylinder (5B, 30B, 48Y)",
            "template": "uf6_cylinder",
            "applications": "5B, 30B, 48Y, 48X shipping/storage cylinders",
            "geometry": "Standard UF6 cylinder per ANSI N14.1 specifications",
            "key_params": "cylinder_type, enrichment, fill_fraction",
            "image_height": 280,
        },
        {
            "name": "Rectangular Box",
            "template": "rectangular_box",
            "applications": "Chemical traps, HEPA filters, rectangular GEVS components",
            "geometry": "Rectangular parallelepiped (box) with wall and reflector",
            "key_params": "length_cm, width_cm, height_cm",
            "image_height": 280,
        },
        {
            "name": "2D Cylinder Array",
            "template": "cylinder_array",
            "applications": "Cassette spacing, piping spacing, RUTS trap spacing",
            "geometry": "Rectangular array of identical cylinders (single layer)",
            "key_params": "rows, cols, gap_cm (edge-to-edge)",
            "image_height": 280,
        },
        {
            "name": "3D Cylinder Array (Stacked)",
            "template": "cylinder_array_3d",
            "applications": "Stacked shipping cylinders (2-3 high), storage arrays",
            "geometry": "3D array with floor modeling (rows × cols × layers)",
            "key_params": "rows, cols, layers, gap_x_cm, gap_y_cm, gap_z_cm",
            "image_height": 280,
        },
    ]

    for app in applications:
        # Application header
        ws2[f'A{row}'] = app["name"]
        ws2[f'A{row}'].font = Font(bold=True, size=12)
        ws2[f'A{row}'].fill = light_blue_fill
        ws2.merge_cells(f'A{row}:H{row}')
        row += 1

        # Details
        ws2[f'A{row}'] = "Template:"
        ws2[f'A{row}'].font = bold_font
        ws2[f'B{row}'] = app["template"]
        row += 1

        ws2[f'A{row}'] = "Applications:"
        ws2[f'A{row}'].font = bold_font
        ws2[f'B{row}'] = app["applications"]
        ws2.merge_cells(f'B{row}:H{row}')
        row += 1

        ws2[f'A{row}'] = "Geometry:"
        ws2[f'A{row}'].font = bold_font
        ws2[f'B{row}'] = app["geometry"]
        ws2.merge_cells(f'B{row}:H{row}')
        row += 1

        ws2[f'A{row}'] = "Key Parameters:"
        ws2[f'A{row}'].font = bold_font
        ws2[f'B{row}'] = app["key_params"]
        ws2.merge_cells(f'B{row}:H{row}')
        row += 1

        # Image row - add labels
        ws2[f'A{row}'] = "2D Cross-Sections:"
        ws2[f'A{row}'].font = Font(bold=True, size=10)
        ws2[f'E{row}'] = "3D Voxel View:"
        ws2[f'E{row}'].font = Font(bold=True, size=10)
        row += 1

        # Get image paths
        template = app["template"]
        img_2d_path, img_3d_path = IMAGE_PATHS.get(template, (None, None))

        image_start_row = row

        # Insert 2D geometry image
        if img_2d_path and img_2d_path.exists():
            try:
                img_2d = Image(str(img_2d_path))
                # Scale image to fit
                scale = app["image_height"] / img_2d.height
                img_2d.width = int(img_2d.width * scale)
                img_2d.height = app["image_height"]
                ws2.add_image(img_2d, f'A{row}')
            except Exception as e:
                ws2[f'A{row}'] = f"[Image not found: {img_2d_path.name}]"
                ws2[f'A{row}'].font = Font(italic=True, color='808080')
        else:
            ws2[f'A{row}'] = "[2D image not available]"
            ws2[f'A{row}'].font = Font(italic=True, color='808080')

        # Insert 3D voxel image
        if img_3d_path and img_3d_path.exists():
            try:
                img_3d = Image(str(img_3d_path))
                # Scale image to fit
                scale = app["image_height"] / img_3d.height
                img_3d.width = int(img_3d.width * scale)
                img_3d.height = app["image_height"]
                ws2.add_image(img_3d, f'E{row}')
            except Exception as e:
                ws2[f'E{row}'] = f"[Image not found: {img_3d_path.name}]"
                ws2[f'E{row}'].font = Font(italic=True, color='808080')
        else:
            ws2[f'E{row}'] = "[3D image not available]"
            ws2[f'E{row}'].font = Font(italic=True, color='808080')

        # Set row heights for image area (roughly 15 pixels per row)
        rows_for_image = app["image_height"] // 15 + 2
        for img_row in range(row, row + rows_for_image):
            ws2.row_dimensions[img_row].height = 15

        row += rows_for_image + 2  # Extra spacing between applications

    # =========================================================================
    # TAB 3: Request Form
    # =========================================================================
    ws3 = wb.create_sheet("Request Form")

    ws3['A1'] = "ANALYSIS REQUEST FORM"
    ws3['A1'].font = Font(bold=True, size=18)
    ws3.merge_cells('A1:P1')

    ws3['A3'] = "Fill one row per analysis. Use comma-separated values for parameter sweeps (e.g., '5, 10, 15, 20')."
    ws3['A3'].alignment = wrap_alignment
    ws3.merge_cells('A3:P3')

    # Header row
    headers = [
        ("A", "Request ID", "Your tracking ID"),
        ("B", "Application", "From catalog"),
        ("C", "Description", "Brief description"),
        ("D", "Enrichment\n(wt% U-235)", "REQUIRED"),
        ("E", "Dimension 1\n(cm)", "Radius or Length"),
        ("F", "Dimension 2\n(cm)", "Height or Width"),
        ("G", "Dimension 3\n(cm)", "Height (for box)"),
        ("H", "Cylinder Type", "5B, 30B, 48Y, etc."),
        ("I", "Array: Rows", "For arrays"),
        ("J", "Array: Cols", "For arrays"),
        ("K", "Array: Layers", "For 3D arrays"),
        ("L", "Gap (cm)", "Edge-to-edge spacing"),
        ("M", "Wall Material", "See Reference tab"),
        ("N", "Reflector", "water/concrete/air/none"),
        ("O", "Priority", "High/Medium/Low"),
        ("P", "Notes", "Special requirements"),
    ]

    for col, header, tooltip in headers:
        cell = ws3[f'{col}5']
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        cell.border = thin_border
        # Add tooltip as comment in row 4
        ws3[f'{col}4'] = tooltip
        ws3[f'{col}4'].font = Font(italic=True, size=9, color='666666')
        ws3[f'{col}4'].alignment = center_alignment

    ws3.row_dimensions[5].height = 40

    # Example rows
    examples = [
        ("EX-001", "Single Cylinder", "Cold trap - 10cm radius", "20", "10", "50", "", "", "", "", "", "", "steel", "water", "Medium", "Example entry"),
        ("EX-002", "Shipping Cylinder", "30B at various enrichments", "5, 10, 15, 20", "", "", "", "30b", "", "", "", "", "", "water", "High", "Enrichment sweep"),
        ("EX-003", "Rectangular Box", "HEPA filter housing", "20", "60", "40", "30", "", "", "", "", "", "steel", "water", "Medium", ""),
        ("EX-004", "3D Cylinder Array", "Stacked 48Y storage", "5", "", "", "", "48y", "2", "2", "2", "10", "", "concrete", "High", "Min spacing study"),
    ]

    for i, example in enumerate(examples, start=6):
        for j, value in enumerate(example):
            cell = ws3[f'{get_column_letter(j+1)}{i}']
            cell.value = value
            cell.border = thin_border
            if i == 6:  # First example highlighted
                cell.fill = light_yellow_fill

    # Empty rows for input
    for i in range(10, 30):
        for j in range(1, 17):
            cell = ws3[f'{get_column_letter(j)}{i}']
            cell.border = thin_border

    # Set column widths
    col_widths = [12, 18, 25, 12, 12, 12, 12, 12, 10, 10, 10, 10, 12, 12, 10, 25]
    for i, width in enumerate(col_widths, start=1):
        ws3.column_dimensions[get_column_letter(i)].width = width

    # =========================================================================
    # TAB 4: Reference - Cylinders
    # =========================================================================
    ws4 = wb.create_sheet("Reference - Cylinders")

    ws4['A1'] = "STANDARD UF6 CYLINDER SPECIFICATIONS"
    ws4['A1'].font = Font(bold=True, size=18)
    ws4.merge_cells('A1:H1')

    ws4['A3'] = "Per ANSI N14.1 - these are the cylinder types available in the uf6_cylinder and cylinder_array templates."
    ws4.merge_cells('A3:H3')

    # Cylinder table header
    cyl_headers = ["Cylinder", "Outer Dia (cm)", "Wall (cm)", "Int. Height (cm)", "Wall Material", "Max Fill (kg)", "Typical Use"]
    for i, header in enumerate(cyl_headers, start=1):
        cell = ws4[f'{get_column_letter(i)}5']
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.border = thin_border

    # Cylinder data
    cylinders = [
        ("1S", "12.70", "0.16", "22.9", "Steel", "2.2", "Samples"),
        ("2S", "12.70", "0.16", "58.4", "Steel", "5.0", "Samples"),
        ("5A", "12.70", "0.79", "94.0", "Monel", "25.0", "HALEU transport"),
        ("5B", "12.70", "0.79", "94.0", "Monel", "25.0", "HALEU transport"),
        ("30B", "76.20", "1.27", "206.0", "Steel", "2277.0", "LEU transport/storage"),
        ("48X", "122.24", "1.59", "302.0", "Steel", "12,501", "Tails storage"),
        ("48Y", "122.24", "1.59", "302.0", "Steel", "12,501", "Feed/product storage"),
        ("48G", "122.24", "1.59", "302.0", "Steel", "12,501", "Heels cylinder"),
    ]

    for i, cyl in enumerate(cylinders, start=6):
        for j, value in enumerate(cyl, start=1):
            cell = ws4[f'{get_column_letter(j)}{i}']
            cell.value = value
            cell.border = thin_border
            if cyl[0] in ['5A', '5B', '30B', '48Y']:  # Highlight common ones
                cell.fill = light_green_fill

    ws4['A16'] = "Note: Highlighted cylinders are the most commonly used for enrichment facility analyses."
    ws4['A16'].font = Font(italic=True)

    # Set column widths
    for i, width in enumerate([10, 14, 12, 14, 14, 14, 25], start=1):
        ws4.column_dimensions[get_column_letter(i)].width = width

    # =========================================================================
    # TAB 5: Reference - Materials
    # =========================================================================
    ws5 = wb.create_sheet("Reference - Materials")

    ws5['A1'] = "AVAILABLE MATERIALS"
    ws5['A1'].font = Font(bold=True, size=18)
    ws5.merge_cells('A1:E1')

    # Wall materials
    ws5['A3'] = "Wall Materials"
    ws5['A3'].font = header_font

    wall_headers = ["Material", "Keyword", "Density (g/cc)", "Typical Use"]
    for i, header in enumerate(wall_headers, start=1):
        cell = ws5[f'{get_column_letter(i)}4']
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.border = thin_border

    wall_materials = [
        ("Carbon Steel", "steel", "7.82", "Process piping, vessels"),
        ("Stainless Steel 304", "ss304", "8.03", "Corrosion-resistant equipment"),
        ("Aluminum", "aluminum", "2.70", "Lightweight containers"),
        ("Monel 400", "monel", "8.80", "5A/5B cylinders (HALEU)"),
    ]

    for i, mat in enumerate(wall_materials, start=5):
        for j, value in enumerate(mat, start=1):
            cell = ws5[f'{get_column_letter(j)}{i}']
            cell.value = value
            cell.border = thin_border

    # Reflector materials
    ws5['A11'] = "Reflector Materials"
    ws5['A11'].font = header_font

    refl_headers = ["Material", "Keyword", "Density (g/cc)", "Notes"]
    for i, header in enumerate(refl_headers, start=1):
        cell = ws5[f'{get_column_letter(i)}12']
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.border = thin_border

    refl_materials = [
        ("Water", "water", "1.00", "Most reactive - conservative default"),
        ("Concrete", "concrete", "2.30", "Building/floor structures"),
        ("Air", "air", "0.001", "Minimal reflection"),
        ("None", "none", "-", "Bare/unreflected (vacuum BC)"),
    ]

    for i, mat in enumerate(refl_materials, start=13):
        for j, value in enumerate(mat, start=1):
            cell = ws5[f'{get_column_letter(j)}{i}']
            cell.value = value
            cell.border = thin_border
            if mat[1] == "water":
                cell.fill = light_green_fill

    ws5['A19'] = "Default: Water reflection is used unless otherwise specified (conservative assumption)."
    ws5['A19'].font = Font(italic=True)

    # Set column widths
    for i, width in enumerate([18, 12, 14, 40], start=1):
        ws5.column_dimensions[get_column_letter(i)].width = width

    # Save
    output_path = BASE_PATH / "docs" / "Criticality_Analysis_Request_Form_v2.xlsx"
    wb.save(output_path)
    print(f"Created: {output_path}")

    # Print image status
    print("\nImage embedding status:")
    for template, (img_2d, img_3d) in IMAGE_PATHS.items():
        status_2d = "OK" if img_2d.exists() else "MISSING"
        status_3d = "OK" if img_3d.exists() else "MISSING"
        print(f"  {template}: 2D={status_2d}, 3D={status_3d}")

    return output_path


if __name__ == "__main__":
    create_form()
