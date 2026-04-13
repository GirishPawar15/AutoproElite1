"""
E-Bill PDF Generator for AutoPro Elite
Generates professional PDF invoices for car and spare part purchases
"""

import os
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.conf import settings


class EBillGenerator:
    """Generate professional PDF bills for orders"""
    
    def __init__(self, order):
        self.order = order
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Tagline style
        self.styles.add(ParagraphStyle(
            name='Tagline',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        # Bill title style
        self.styles.add(ParagraphStyle(
            name='BillTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4,
            fontName='Helvetica'
        ))
        
        # Right aligned text
        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        ))
    
    def _format_currency(self, amount):
        """Format amount as Indian currency"""
        try:
            return f"₹{float(amount):,.2f}"
        except:
            return f"₹0.00"
    
    def _format_date(self, date_obj):
        """Format date in readable format"""
        if not date_obj:
            return datetime.now().strftime("%d %B, %Y")
        return date_obj.strftime("%d %B, %Y")
    
    def generate_pdf(self, output_path):
        """Generate the PDF bill"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Header
        story.extend(self._build_header())
        story.append(Spacer(1, 0.3*inch))
        
        # Bill info and customer details
        story.extend(self._build_info_section())
        story.append(Spacer(1, 0.3*inch))
        
        # Items table
        story.extend(self._build_items_table())
        story.append(Spacer(1, 0.3*inch))
        
        # Totals
        story.extend(self._build_totals_section())
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.extend(self._build_footer())
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_decorations, onLaterPages=self._add_page_decorations)
        
        return output_path
    
    def _build_header(self):
        """Build header with company info"""
        elements = []
        
        # Company name
        elements.append(Paragraph("AutoPro Elite", self.styles['CompanyName']))
        
        # Tagline
        elements.append(Paragraph("Premium Automotive Solutions", self.styles['Tagline']))
        
        # Horizontal line
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_info_section(self):
        """Build bill info and customer details section"""
        elements = []
        
        # Bill title
        bill_type = "TAX INVOICE" if self.order.order_type == "car" else "INVOICE"
        elements.append(Paragraph(bill_type, self.styles['BillTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create two-column layout for bill info and customer details
        bill_info_data = [
            ['<b>Bill Number:</b>', self.order.bill_number or f"APE-{self.order.id:06d}"],
            ['<b>Bill Date:</b>', self._format_date(self.order.bill_date or self.order.created_at)],
            ['<b>Order ID:</b>', f"#{self.order.id}"],
            ['<b>Order Type:</b>', self.order.get_order_type_display()],
            ['<b>Payment Method:</b>', (self.order.payment_method or 'COD').upper()],
        ]
        
        customer_info_data = [
            ['<b>Customer Name:</b>', self.order.customer_name or self.order.user.get_full_name() or self.order.user.username],
            ['<b>Email:</b>', self.order.customer_email or self.order.user.email],
            ['<b>Phone:</b>', self.order.customer_phone or 'N/A'],
            ['<b>Address:</b>', self.order.delivery_address or 'N/A'],
        ]
        
        # Create tables
        bill_info_table = Table(bill_info_data, colWidths=[1.5*inch, 2*inch])
        bill_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        customer_info_table = Table(customer_info_data, colWidths=[1.3*inch, 2.2*inch])
        customer_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        # Combine in a main table
        main_table = Table([[bill_info_table, customer_info_table]], colWidths=[3.5*inch, 3.5*inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(main_table)
        
        return elements
    
    def _build_items_table(self):
        """Build items table"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Order Items", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Table header
        data = [['#', 'Item Description', 'Qty', 'Unit Price', 'Amount']]
        
        # Add items
        for idx, item in enumerate(self.order.items.all(), 1):
            data.append([
                str(idx),
                item.name,
                str(item.quantity),
                self._format_currency(item.price),
                self._format_currency(float(item.price) * item.quantity)
            ])
        
        # Create table
        table = Table(data, colWidths=[0.5*inch, 3.5*inch, 0.7*inch, 1.3*inch, 1.3*inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # # column
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Qty column
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),  # Price columns
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_totals_section(self):
        """Build totals section"""
        elements = []
        
        # Calculate totals
        subtotal = float(self.order.subtotal) if self.order.subtotal else float(self.order.total_amount)
        tax_amount = float(self.order.tax_amount) if hasattr(self.order, 'tax_amount') else 0
        delivery_charge = float(self.order.delivery_charge) if hasattr(self.order, 'delivery_charge') else 0
        total = float(self.order.total_amount)
        
        # Build totals data
        totals_data = []
        
        if subtotal > 0:
            totals_data.append(['Subtotal:', self._format_currency(subtotal)])
        
        if delivery_charge > 0:
            totals_data.append(['Delivery Charge:', self._format_currency(delivery_charge)])
        
        if tax_amount > 0:
            totals_data.append(['Tax (GST):', self._format_currency(tax_amount)])
        
        totals_data.append(['<b>Total Amount:</b>', f'<b>{self._format_currency(total)}</b>'])
        
        # Create table
        totals_table = Table(totals_data, colWidths=[5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2563eb')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f9ff')),
        ]))
        
        elements.append(totals_table)
        
        return elements
    
    def _build_footer(self):
        """Build footer with terms and thank you message"""
        elements = []
        
        # Thank you message
        elements.append(Spacer(1, 0.3*inch))
        thank_you = Paragraph(
            "<b>Thank you for choosing AutoPro Elite!</b>",
            self.styles['BillTitle']
        )
        elements.append(thank_you)
        
        # Terms and conditions
        elements.append(Spacer(1, 0.2*inch))
        terms_style = ParagraphStyle(
            name='Terms',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        terms_text = """
        <b>Terms & Conditions:</b> All sales are final. Returns accepted within 7 days with original packaging.
        Warranty terms apply as per manufacturer guidelines. For support, contact us at support@autoproelite.com
        """
        elements.append(Paragraph(terms_text, terms_style))
        
        # Contact info
        elements.append(Spacer(1, 0.1*inch))
        contact_text = """
        AutoPro Elite | Email: info@autoproelite.com | Phone: +91-1234567890 | Website: www.autoproelite.com
        """
        elements.append(Paragraph(contact_text, terms_style))
        
        return elements
    
    def _add_page_decorations(self, canvas, doc):
        """Add decorative elements to each page"""
        canvas.saveState()
        
        # Add header line
        canvas.setStrokeColor(colors.HexColor('#2563eb'))
        canvas.setLineWidth(3)
        canvas.line(0.75*inch, self.height - 0.5*inch, self.width - 0.75*inch, self.height - 0.5*inch)
        
        # Add footer line
        canvas.setLineWidth(1)
        canvas.line(0.75*inch, 0.5*inch, self.width - 0.75*inch, 0.5*inch)
        
        # Add page number
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        page_num = f"Page {doc.page}"
        canvas.drawRightString(self.width - 0.75*inch, 0.4*inch, page_num)
        
        # Add watermark
        canvas.setFont('Helvetica-Bold', 60)
        canvas.setFillColor(colors.HexColor('#f0f9ff'))
        canvas.saveState()
        canvas.translate(self.width/2, self.height/2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "AutoPro Elite")
        canvas.restoreState()
        
        canvas.restoreState()


def generate_bill_number(order):
    """Generate unique bill number"""
    date_str = datetime.now().strftime("%Y%m%d")
    base_number = f"APE-{date_str}-{order.id:06d}"
    
    # Check if this bill number already exists
    from .models import Order
    counter = 0
    bill_number = base_number
    
    while Order.objects.filter(bill_number=bill_number).exclude(id=order.id).exists():
        counter += 1
        bill_number = f"{base_number}-{counter}"
    
    return bill_number


def generate_ebill_pdf(order):
    """
    Generate e-bill PDF for an order
    Returns the file path of the generated PDF
    """
    # Generate bill number if not exists
    if not order.bill_number:
        order.bill_number = generate_bill_number(order)
        order.bill_date = datetime.now()
        order.save(update_fields=['bill_number', 'bill_date'])
    
    # Define output path
    media_root = getattr(settings, 'MEDIA_ROOT', 'backend/media')
    bills_dir = os.path.join(media_root, 'bills')
    filename = f"bill_{order.bill_number}.pdf"
    output_path = os.path.join(bills_dir, filename)
    
    # Generate PDF
    generator = EBillGenerator(order)
    generator.generate_pdf(output_path)
    
    # Update order with PDF path
    relative_path = f"bills/{filename}"
    order.bill_pdf_path = relative_path
    order.save(update_fields=['bill_pdf_path'])
    
    return output_path
