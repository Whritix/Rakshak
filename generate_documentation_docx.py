"""
High-Fidelity DOCX Documentation Generator for Project Rakshak 2.0
Converts PROJECT_DOCUMENTATION.md into an executive military-grade Microsoft Word Document (.docx)
with professional cover page, styled tables, code blocks, callouts, and typography.
"""
import re
import os
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

ROOT = Path(__file__).resolve().parent
MD_PATH = ROOT / "PROJECT_DOCUMENTATION.md"
DOCX_PATH = ROOT / "PROJECT_DOCUMENTATION.docx"

# Color Palette
COLOR_NAVY = RGBColor(15, 41, 66)       # #0F2942 Primary
COLOR_BLUE = RGBColor(2, 132, 199)      # #0284C7 Accent
COLOR_SLATE = RGBColor(30, 41, 59)      # #1E293B Body Text
COLOR_MUTED = RGBColor(100, 116, 139)   # #64748B Secondary Text
COLOR_GOLD = RGBColor(217, 119, 6)      # #D97706 Warning/Highlight

HEX_NAVY = "0F2942"
HEX_BLUE = "0284C7"
HEX_LIGHT_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_CODE_BG = "F1F5F9"
HEX_CALLOUT_BG = "F0F9FF"
HEX_CALLOUT_BORDER = "0284C7"

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_cell_border(cell, **kwargs):
    """
    kwargs: top, bottom, left, right
    values: dict(sz=4, val='single', color='CBD5E1')
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = parse_xml(f'<{tag} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" w:sz="{edge_data.get("sz", "4")}" w:space="0" w:color="{edge_data.get("color", "CBD5E1")}"/>')
            tcBorders.append(element)
    tcPr.append(tcBorders)

def add_header_footer(doc):
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)
        
        # Header
        header = s.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("PROJECT RAKSHAK 2.0 // C4ISR DEFENSE INTELLIGENCE SPECIFICATION")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED
        
        # Footer
        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        frun1 = fp.add_run("SOVEREIGN DEFENSE SPECIFICATION | TEAM BotS | KLS GIT")
        frun1.font.name = "Segoe UI"
        frun1.font.size = Pt(8.5)
        frun1.font.color.rgb = COLOR_MUTED

def create_cover_page(doc):
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(36)
    p_pre.paragraph_format.space_after = Pt(8)
    r_pre = p_pre.add_run("REPUBLIC OF INDIA // DEFENSE & MARITIME RESEARCH INITIATIVE")
    r_pre.font.name = "Segoe UI Semibold"
    r_pre.font.size = Pt(11)
    r_pre.font.color.rgb = COLOR_BLUE

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("PROJECT RAKSHAK 2.0")
    r_title.bold = True
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(32)
    r_title.font.color.rgb = COLOR_NAVY

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(24)
    r_sub = p_sub.add_run("Sovereign, Air-Gapped Multimodal C4ISR System for Naval & Tactical Army Command")
    r_sub.font.name = "Segoe UI Light"
    r_sub.font.size = Pt(15)
    r_sub.font.color.rgb = COLOR_SLATE

    # Horizontal Divider Line
    t_div = doc.add_table(rows=1, cols=1)
    t_div.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_div = t_div.cell(0, 0)
    c_div.width = Inches(6.5)
    set_cell_background(c_div, HEX_BLUE)
    set_cell_margins(c_div, top=15, bottom=15, left=0, right=0)
    p_div = c_div.paragraphs[0]
    p_div.paragraph_format.space_before = Pt(0)
    p_div.paragraph_format.space_after = Pt(0)

    # Descriptive Lead Paragraph
    p_lead = doc.add_paragraph()
    p_lead.paragraph_format.space_before = Pt(24)
    p_lead.paragraph_format.space_after = Pt(28)
    p_lead.paragraph_format.line_spacing = 1.2
    r_lead = p_lead.add_run(
        "Complete technical system documentation covering end-to-end architecture, dual-engine "
        "YOLO11 neural ensembles, Sentinel-1 SAR CA-CFAR radar backscatter analysis, O(N) spatial "
        "threat grid scoring, sovereign air-gapped doctrinal RAG advisory, kinematic multi-target "
        "tracking, and automated STANAG-compliant tactical situation reporting."
    )
    r_lead.font.name = "Segoe UI"
    r_lead.font.size = Pt(11)
    r_lead.font.color.rgb = COLOR_SLATE

    # Metadata Card Table
    card_table = doc.add_table(rows=7, cols=2)
    card_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Inches(2.2), Inches(4.3)]
    
    metadata = [
        ("PROJECT NAME", "Project Rakshak 2.0 (Tactical Watch & Threat Intelligence)"),
        ("TEAM NAME", "Team BotS"),
        ("TEAM MEMBERS", "Aditya Bajantri, Gagan Bongale, Utsav Nanapur, Misbah Falak, Shalina Maniyar, Niyati Gogri"),
        ("INSTITUTION", "KLS Gogte Institute of Technology, Belagavi"),
        ("OPERATIONAL DOMAIN", "Naval Maritime Surveillance & Army Tactical Ground Reconnaissance"),
        ("DEPLOYMENT TARGET", "Sovereign Air-Gapped Edge (NVIDIA Jetson AGX Orin / Shipboard C2)"),
        ("DATE & VERSION", "March 2026 // Production Release v2.0.0"),
    ]

    for row_idx, (label, val) in enumerate(metadata):
        c0 = card_table.cell(row_idx, 0)
        c1 = card_table.cell(row_idx, 1)
        c0.width, c1.width = widths
        
        bg_col = HEX_LIGHT_BG if row_idx % 2 == 0 else "FFFFFF"
        set_cell_background(c0, bg_col)
        set_cell_background(c1, bg_col)
        set_cell_margins(c0, top=90, bottom=90, left=140, right=140)
        set_cell_margins(c1, top=90, bottom=90, left=140, right=140)
        
        b_spec = dict(sz=4, val='single', color=HEX_BORDER)
        set_cell_border(c0, top=b_spec, bottom=b_spec, left=b_spec, right=b_spec)
        set_cell_border(c1, top=b_spec, bottom=b_spec, left=b_spec, right=b_spec)

        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.bold = True
        r0.font.name = "Segoe UI Semibold"
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = COLOR_NAVY

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_SLATE

    # Page Break after Cover Page
    doc.add_page_break()

def parse_inline_formatting(paragraph, text, default_font="Segoe UI", default_size=10.0, default_color=COLOR_SLATE):
    """Parses bold, code, and italic within a line into formatted runs."""
    pattern = re.compile(r'(\*\*.*?\*\*|`.*?`|\*.*?\*)')
    tokens = pattern.split(text)
    for token in tokens:
        if not token:
            continue
        run = paragraph.add_run()
        run.font.name = default_font
        run.font.size = Pt(default_size)
        run.font.color.rgb = default_color
        
        if token.startswith('**') and token.endswith('**'):
            run.text = token[2:-2]
            run.bold = True
        elif token.startswith('`') and token.endswith('`'):
            run.text = token[1:-1]
            run.font.name = "Consolas"
            run.font.size = Pt(default_size - 0.5)
            run.font.color.rgb = COLOR_NAVY
        elif token.startswith('*') and token.endswith('*'):
            run.text = token[1:-1]
            run.italic = True
        else:
            run.text = token

def add_code_block(doc, code_lines, language=""):
    """Creates a stylized code block container with monospaced text and shaded background."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, HEX_CODE_BG)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    b_spec = dict(sz=4, val='single', color=HEX_BORDER)
    set_cell_border(cell, top=b_spec, bottom=b_spec, left=b_spec, right=b_spec)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05

    for idx, line in enumerate(code_lines):
        if idx > 0:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run.font.color.rgb = COLOR_SLATE

    # Spacer after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(4)
    sp.paragraph_format.space_after = Pt(4)

def add_styled_table(doc, headers, data_rows):
    """Creates a military-grade formatted table with colored headers and alternating rows."""
    col_count = len(headers)
    tbl = doc.add_table(rows=len(data_rows) + 1, cols=col_count)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    col_width = Inches(6.5 / max(1, col_count))

    # Header Row
    for col_idx, header_text in enumerate(headers):
        cell = tbl.cell(0, col_idx)
        cell.width = col_width
        set_cell_background(cell, HEX_NAVY)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        b_spec = dict(sz=4, val='single', color="0A192F")
        set_cell_border(cell, top=b_spec, bottom=b_spec, left=b_spec, right=b_spec)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(header_text.strip())
        run.bold = True
        run.font.name = "Segoe UI Semibold"
        run.font.size = Pt(9.0)
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for row_idx, row_data in enumerate(data_rows):
        bg = HEX_LIGHT_BG if row_idx % 2 == 0 else "FFFFFF"
        for col_idx in range(col_count):
            cell = tbl.cell(row_idx + 1, col_idx)
            cell.width = col_width
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            b_spec = dict(sz=4, val='single', color=HEX_BORDER)
            set_cell_border(cell, top=b_spec, bottom=b_spec, left=b_spec, right=b_spec)

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
            parse_inline_formatting(p, cell_text.strip(), default_font="Segoe UI", default_size=8.5, default_color=COLOR_SLATE)

    # Spacer after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(4)
    sp.paragraph_format.space_after = Pt(4)

def generate_docx():
    print(f"Reading markdown source from {MD_PATH}...")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing {MD_PATH}")

    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = Document()
    add_header_footer(doc)
    create_cover_page(doc)

    lines = md_text.splitlines()
    in_code_block = False
    code_lines = []
    code_lang = ""

    in_table = False
    table_headers = []
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            else:
                in_code_block = False
                add_code_block(doc, code_lines, code_lang)
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle Tables
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            # Check if separator row (e.g. |---|---|)
            if all(re.match(r'^:?-+:?$', c) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_headers = cells
                table_rows = []
            else:
                table_rows.append(cells)
            continue
        elif in_table:
            # End of table
            in_table = False
            add_styled_table(doc, table_headers, table_rows)
            table_headers = []
            table_rows = []

        # Ignore empty lines or pure dividers
        if not stripped or stripped == '---':
            continue

        # Headings
        if stripped.startswith('# '):
            # Document title already in cover page, skip or style as header
            continue
        elif stripped.startswith('## '):
            heading_text = stripped[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(22)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(heading_text)
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(16.0)
            run.font.color.rgb = COLOR_NAVY
            continue
        elif stripped.startswith('### '):
            heading_text = stripped[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(heading_text)
            run.bold = True
            run.font.name = "Segoe UI Semibold"
            run.font.size = Pt(12.5)
            run.font.color.rgb = COLOR_BLUE
            continue
        elif stripped.startswith('#### '):
            heading_text = stripped[5:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(heading_text)
            run.bold = True
            run.font.name = "Segoe UI Semibold"
            run.font.size = Pt(10.5)
            run.font.color.rgb = COLOR_NAVY
            continue

        # Bullet Lists
        if stripped.startswith('- ') or stripped.startswith('* '):
            bullet_text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, bullet_text, default_font="Segoe UI", default_size=9.5, default_color=COLOR_SLATE)
            continue

        # Numbered Lists
        num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if num_match:
            num = num_match.group(1)
            item_text = num_match.group(2)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, item_text, default_font="Segoe UI", default_size=9.5, default_color=COLOR_SLATE)
            continue

        # Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        parse_inline_formatting(p, stripped, default_font="Segoe UI", default_size=9.5, default_color=COLOR_SLATE)

    # In case a table was open at EOF
    if in_table and table_headers:
        add_styled_table(doc, table_headers, table_rows)

    doc.save(str(DOCX_PATH))
    print(f"Successfully created high-fidelity DOCX documentation at: {DOCX_PATH}")

if __name__ == "__main__":
    generate_docx()
