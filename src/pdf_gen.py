from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import io
import pandas as pd

def generate_pdf_report(overall_score, area_scores, factor_scores, gaps_df, cycle_id):
    """Generate a comprehensive PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0033A0'),
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0033A0'),
        spaceBefore=20,
        spaceAfter=12
    )

    elements = []
    
    # --- Title Page ---
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("RMM Maturity Assessment Report", title_style))
    elements.append(Paragraph(f"Cycle: {cycle_id}", styles['Normal']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Spacer(1, 1*inch))
    
    # Overall Score
    score_text = f"Overall Maturity: {overall_score['overall_index']:.2f} / 5.0"
    elements.append(Paragraph(score_text, heading_style))
    elements.append(Paragraph(f"Assessment Level: {overall_score['overall_level']}", styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    
    # --- Area Scores Table ---
    elements.append(Paragraph("Area Breakdown", heading_style))
    
    data = [['Area', 'Score', 'Level']]
    for _, row in area_scores.iterrows():
        data.append([
            row['area'],
            f"{row['area_index']:.2f}",
            f"{row['area_level']}"
        ])
        
    t = Table(data, colWidths=[3*inch, 1*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0033A0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*inch))
    
    # --- Priority Gaps ---
    elements.append(Paragraph("Priority Improvement Opportunities", heading_style))
    
    if len(gaps_df) > 0:
        gap_data = [['Factor', 'Gap', 'Recommendation']]
        for i, row in gaps_df.head(10).iterrows():
            gap_data.append([
                Paragraph(row['factor_name'], styles['Normal']),
                f"{row['gap_levels']}",
                Paragraph(row['action_text'], styles['Normal'])
            ])
            
        t_gaps = Table(gap_data, colWidths=[2.5*inch, 0.5*inch, 3.5*inch])
        t_gaps.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E31837')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(t_gaps)
    else:
        elements.append(Paragraph("No significant gaps identified.", styles['Normal']))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
