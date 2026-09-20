import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import sanchay_db

def generate_client_statement(client_id: int, target_advisor_id=None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    title_style.textColor = colors.HexColor("#1e293b")
    subtitle_style = styles['Heading2']
    subtitle_style.textColor = colors.HexColor("#334155")
    normal_style = styles['Normal']
    
    elements = []
    
    with sanchay_db.get_connection() as conn:
        client_row = conn.execute('''
            SELECT c.*, u.name, u.email, u.phone
            FROM clients c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.client_id = ? AND (? IS NULL OR c.advisor_id = ?)
        ''', (client_id, target_advisor_id, target_advisor_id)).fetchone()
        
        if not client_row:
            return None # Client not found or access denied
            
        # Get portfolio summary
        portfolios = conn.execute('''
            SELECT 'Main Portfolio' as portfolio_name, SUM(h.quantity * COALESCE(ap.price, h.avg_buy_price)) as value
            FROM portfolios p
            JOIN holdings h ON p.portfolio_id = h.portfolio_id
            LEFT JOIN asset_master am ON h.asset_id = am.asset_id
            LEFT JOIN asset_prices ap ON am.asset_id = ap.asset_id 
                AND ap.price_id = (SELECT price_id FROM asset_prices WHERE asset_id = am.asset_id ORDER BY price_date DESC LIMIT 1)
            WHERE p.client_id = ?
            GROUP BY p.portfolio_id
        ''', (client_id,)).fetchall()
        
        total_value = sum((float(p['value']) if p['value'] else 0) for p in portfolios)
        
        # Get Holdings
        holdings = conn.execute('''
            SELECT 'TICKER' as ticker, am.asset_name as name, ac.category_name, h.quantity, COALESCE(ap.price, h.avg_buy_price) as current_price, (h.quantity * COALESCE(ap.price, h.avg_buy_price)) as total_value
            FROM holdings h
            JOIN asset_master am ON h.asset_id = am.asset_id
            JOIN asset_categories ac ON am.category_id = ac.category_id
            LEFT JOIN asset_prices ap ON am.asset_id = ap.asset_id
                AND ap.price_id = (SELECT price_id FROM asset_prices WHERE asset_id = am.asset_id ORDER BY price_date DESC LIMIT 1)
            JOIN portfolios p ON h.portfolio_id = p.portfolio_id
            WHERE p.client_id = ?
            ORDER BY total_value DESC
        ''', (client_id,)).fetchall()
        
        if not holdings:
            raise ValueError("No holdings available to generate report")
        
        # Header
        elements.append(Paragraph("Sanchay IAS", title_style))
        elements.append(Paragraph("Monthly Wealth Statement", title_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Client Info Table
        info_data = [
            [Paragraph(f"<b>Client:</b> {client_row['name']}", normal_style), Paragraph(f"<b>Statement Date:</b> {datetime.date.today().strftime('%B %d, %Y')}", normal_style)],
            [Paragraph(f"<b>Email:</b> {client_row['email']}", normal_style), Paragraph(f"<b>Total Net Worth:</b> ${total_value:,.2f}", normal_style)]
        ]
        info_table = Table(info_data, colWidths=[3.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.4 * inch))
        
        # Holdings Table
        elements.append(Paragraph("Asset Allocation & Current Holdings", subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        table_data = [["Asset", "Category", "Quantity", "Current Price", "Total Value"]]
        for h in holdings:
            table_data.append([
                f"{h['name']} ({h['ticker']})",
                h['category_name'],
                f"{float(h['quantity']):,.2f}",
                f"${float(h['current_price']):,.2f}",
                f"${float(h['total_value']):,.2f}"
            ])
            
        if len(table_data) > 1:
            t = Table(table_data, colWidths=[2.6*inch, 1.2*inch, 1*inch, 1.1*inch, 1.2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f8fafc")])
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("No holdings found for this client.", normal_style))
            
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("<font color='gray'>This statement is generated electronically and is for informational purposes only.</font>", normal_style))
            
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
