"""
Certificate Generation Service
Creates PDF certificates for disk erasure operations with QR codes
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import qrcode
import io
import os
import hashlib
import json

class CertificateGenerator:
    def __init__(self, output_dir='../data/certificates'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_certificate(self, wipe_report, device_info, ledger_entry=None):
        """
        Generate a PDF certificate for disk erasure
        
        Args:
            wipe_report: Report from wipe operation
            device_info: Device information (model, serial, etc.)
            ledger_entry: Optional blockchain/ledger entry for verification
        
        Returns:
            dict with certificate_path, certificate_hash, qr_code_data
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cert_filename = f"cert_{device_info['serial']}_{timestamp}.pdf"
        cert_path = os.path.join(self.output_dir, cert_filename)
        
        # Create certificate
        doc = SimpleDocTemplate(cert_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        story.append(Paragraph("CERTIFICATE OF SECURE DATA ERASURE", title_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # Warning banner
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5
        )
        story.append(Paragraph("⚠ IRREVERSIBLE ERASURE PERFORMED ⚠", warning_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # Certificate ID and Date
        cert_id = self._generate_cert_id(device_info, wipe_report)
        story.append(Paragraph(f"<b>Certificate ID:</b> {cert_id}", styles['Normal']))
        story.append(Paragraph(f"<b>Issue Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Device Information Section
        story.append(Paragraph("Device Information", heading_style))
        device_data = [
            ['Device Path:', device_info.get('name', 'N/A')],
            ['Model:', device_info.get('model', 'Unknown')],
            ['Serial Number:', device_info.get('serial', 'N/A')],
            ['Capacity:', device_info.get('size', 'Unknown')],
            ['Type:', device_info.get('type', 'Unknown')],
            ['Transport:', device_info.get('transport', 'Unknown')]
        ]
        device_table = Table(device_data, colWidths=[2*inch, 4*inch])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(device_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Erasure Details Section
        story.append(Paragraph("Erasure Operation Details", heading_style))
        erasure_data = [
            ['Wipe ID:', wipe_report.get('wipe_id', 'N/A')],
            ['Method:', wipe_report.get('method', 'Unknown').upper()],
            ['Start Time:', wipe_report.get('start_time', 'N/A')],
            ['End Time:', wipe_report.get('end_time', 'N/A')],
            ['Duration:', wipe_report.get('duration', 'N/A')],
            ['Status:', wipe_report.get('status', 'Unknown').upper()],
            ['Verification:', wipe_report.get('verification', 'N/A')],
            ['Mode:', 'SIMULATED' if wipe_report.get('simulated', False) else 'REAL']
        ]
        erasure_table = Table(erasure_data, colWidths=[2*inch, 4*inch])
        erasure_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(erasure_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Blockchain/Ledger Section (if available)
        if ledger_entry:
            story.append(Paragraph("Blockchain Verification", heading_style))
            ledger_data = [
                ['Ledger Type:', ledger_entry.get('ledger_type', 'Local')],
                ['Block Hash:', ledger_entry.get('block_hash', 'N/A')[:32] + '...'],
                ['Transaction ID:', ledger_entry.get('transaction_id', 'N/A')],
                ['Timestamp:', ledger_entry.get('timestamp', 'N/A')],
            ]
            ledger_table = Table(ledger_data, colWidths=[2*inch, 4*inch])
            ledger_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(ledger_table)
            story.append(Spacer(1, 0.2 * inch))
        
        # Certificate Hash
        cert_data = {
            'device': device_info,
            'wipe': wipe_report,
            'cert_id': cert_id
        }
        cert_hash = self._calculate_hash(cert_data)
        
        story.append(Paragraph("Certificate Integrity", heading_style))
        story.append(Paragraph(f"<b>SHA-256 Hash:</b>", styles['Normal']))
        story.append(Paragraph(f"<font size=8>{cert_hash}</font>", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Generate QR Code with verification URL
        verification_url = f"https://verify.erash.local/cert/{cert_id}"
        qr_data = {
            'cert_id': cert_id,
            'serial': device_info.get('serial', 'N/A'),
            'hash': cert_hash,
            'verify_url': verification_url
        }
        
        qr_img = self._generate_qr_code(json.dumps(qr_data))
        story.append(Paragraph("Verification QR Code", heading_style))
        story.append(Paragraph(f"Scan to verify: {verification_url}", styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Add QR code image
        img = Image(qr_img, width=2*inch, height=2*inch)
        story.append(img)
        story.append(Spacer(1, 0.2 * inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(
            "This certificate confirms that the above device has been securely erased using industry-standard methods.",
            footer_style
        ))
        story.append(Paragraph(
            f"Generated by ERASH v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        
        return {
            'certificate_path': cert_path,
            'certificate_filename': cert_filename,
            'certificate_id': cert_id,
            'certificate_hash': cert_hash,
            'qr_code_data': qr_data,
            'verification_url': verification_url
        }
    
    def _generate_cert_id(self, device_info, wipe_report):
        """Generate unique certificate ID"""
        data = f"{device_info.get('serial', 'UNKNOWN')}_{wipe_report.get('wipe_id', '')}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    def _calculate_hash(self, data):
        """Calculate SHA-256 hash of certificate data"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _generate_qr_code(self, data):
        """Generate QR code image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to BytesIO for ReportLab
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer
    
    def generate_bulk_certificate(self, wipe_reports, device_infos, job_id):
        """Generate a single certificate for multiple device erasures (bulk job)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cert_filename = f"cert_bulk_{job_id}_{timestamp}.pdf"
        cert_path = os.path.join(self.output_dir, cert_filename)
        
        doc = SimpleDocTemplate(cert_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("BULK ERASURE CERTIFICATE", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Job Info
        story.append(Paragraph(f"<b>Job ID:</b> {job_id}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"<b>Total Devices:</b> {len(wipe_reports)}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Device Summary Table
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("Erased Devices", heading_style))
        
        table_data = [['#', 'Serial Number', 'Model', 'Type', 'Status']]
        for idx, (report, device) in enumerate(zip(wipe_reports, device_infos), 1):
            table_data.append([
                str(idx),
                device.get('serial', 'N/A')[:20],
                device.get('model', 'Unknown')[:25],
                device.get('type', 'Unknown'),
                report.get('status', 'Unknown').upper()
            ])
        
        device_table = Table(table_data, colWidths=[0.5*inch, 1.8*inch, 2*inch, 0.8*inch, 1*inch])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(device_table)
        
        # Build PDF
        doc.build(story)
        
        return {
            'certificate_path': cert_path,
            'certificate_filename': cert_filename,
            'job_id': job_id,
            'device_count': len(wipe_reports)
        }
