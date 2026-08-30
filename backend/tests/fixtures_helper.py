# backend/tests/fixtures_helper.py
"""
Test Fixtures Generator for SOVEREIGN-X
Generates small in-memory/on-disk test documents:
- Digital vector PDF with text and tables
- Scanned-style image-only PDF
- Multi-sheet Excel workbook (.xlsx)
- Tabular CSV
- UTF-8 text document
"""

from pathlib import Path
import fitz  # PyMuPDF
import openpyxl
from PIL import Image, ImageDraw


def create_sample_digital_pdf(output_path: Path) -> Path:
    """Create a multi-page digital PDF with structural headers and text."""
    doc = fitz.open()

    # Page 1: Inspection Summary
    page1 = doc.new_page()
    page1.insert_text(
        fitz.Point(50, 60),
        "# Section 1.0 Executive Summary\n\n"
        "Plant 4 Reflux Pump 3B was subjected to periodic non-destructive examination.\n"
        "Initial visual inspection indicated normal external conditions.",
        fontsize=12
    )

    # Page 2: Ultrasonic Thickness Gauging Findings
    page2 = doc.new_page()
    page2.insert_text(
        fitz.Point(50, 60),
        "# Section 3.2 Ultrasonic Thickness Gauging\n\n"
        "Measured wall thickness at casing node C-12 was recorded at 3.42 mm.\n"
        "Baseline nominal design thickness is 4.80 mm.\n"
        "Critical wear observed on impeller housing.",
        fontsize=12
    )

    doc.save(output_path)
    doc.close()
    return output_path


def create_sample_scanned_pdf(output_path: Path) -> Path:
    """Create a scanned-style PDF where page contains only an image (no native text)."""
    # Create image with PIL
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 560, 760], outline=(100, 100, 100), width=2)
    draw.text((60, 80), "SCANNED FIELD REPORT - NDT INSPECTION", fill=(0, 0, 0))
    draw.text((60, 120), "Weld Seam Porosity Detected at Joint 4A", fill=(0, 0, 0))
    draw.text((60, 160), "Operator Signoff: J. Doe - Grade II Inspector", fill=(0, 0, 0))

    img_path = output_path.parent / "temp_scan.png"
    img.save(img_path)

    # Embed into PDF
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_image(fitz.Rect(0, 0, 600, 800), filename=str(img_path))
    doc.save(output_path)
    doc.close()

    if img_path.exists():
        img_path.unlink()

    return output_path


def create_sample_xlsx(output_path: Path) -> Path:
    """Create a multi-sheet Excel workbook with maintenance history and tolerance tables."""
    wb = openpyxl.Workbook()

    # Sheet 1: Thickness_Log
    ws1 = wb.active
    ws1.title = "Thickness_Log"
    ws1.append(["Year", "Component", "Thickness_mm", "Status"])
    ws1.append([2022, "Pump_3B_Casing", 4.75, "NORMAL"])
    ws1.append([2023, "Pump_3B_Casing", 4.30, "NORMAL"])
    ws1.append([2024, "Pump_3B_Casing", 3.85, "WARNING"])
    ws1.append([2025, "Pump_3B_Casing", 3.42, "CRITICAL"])

    # Sheet 2: OEM_Limits
    ws2 = wb.create_sheet(title="OEM_Limits")
    ws2.append(["Component", "Nominal_mm", "Min_Allowable_mm", "Action"])
    ws2.append(["Pump_3B_Casing", 4.80, 4.00, "MANDATORY_REPLACEMENT"])
    ws2.append(["Impeller_Shaft", 25.0, 22.5, "REPAIR"])

    wb.save(output_path)
    wb.close()
    return output_path


def create_sample_csv(output_path: Path) -> Path:
    """Create a sample CSV file."""
    content = (
        "Date,Sensor_ID,Vibration_mm_s,Temperature_C\n"
        "2026-08-01,VIB-3B-01,2.4,62.5\n"
        "2026-08-15,VIB-3B-01,4.8,78.1\n"
        "2026-08-30,VIB-3B-01,8.9,94.2\n"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


def create_sample_txt(output_path: Path) -> Path:
    """Create a sample UTF-8 plain text file."""
    content = (
        "# Engineering Directive 2026-09\n\n"
        "All centrifugal pumps operating in hydrocarbon service must maintain casing thickness "
        "above manufacturer minimum specified safety thresholds at all times.\n\n"
        "# Section 2 Compliance Requirements\n"
        "Mandatory ultrasonic re-testing is required every 90 days for units showing wear acceleration."
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path
