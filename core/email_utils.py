"""
Email utility for sending e-bills to customers
"""

import os
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string


def send_booking_confirmation_email(*, booking_type, to_email, subject, text_message, html_message=None):
    try:
        if not to_email:
            return False

        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@autoproelite.com'),
            to=[to_email],
        )

        if html_message:
            email.content_subtype = 'html'
            email.body = html_message

        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending booking confirmation email ({booking_type}) to {to_email}: {str(e)}")
        return False


def send_ebill_email(order, pdf_path):
    """
    Send e-bill PDF to customer via email
    
    Args:
        order: Order object
        pdf_path: Path to the generated PDF file
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get customer email
        customer_email = order.customer_email or (order.user.email if order.user else None)
        
        if not customer_email:
            print(f"No email address for order #{order.id}")
            return False
        
        # Get customer name
        customer_name = order.customer_name or (
            order.user.get_full_name() if order.user else None
        ) or (order.user.username if order.user else "Customer")
        
        # Email subject
        subject = f"Your AutoPro Elite Invoice - {order.bill_number}"
        
        # Email body (HTML)
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 5px 0 0 0;
                    opacity: 0.9;
                }}
                .content {{
                    background: #f8fafc;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .order-details {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #2563eb;
                }}
                .order-details h3 {{
                    margin-top: 0;
                    color: #2563eb;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #64748b;
                }}
                .detail-value {{
                    color: #1e293b;
                }}
                .total {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .button {{
                    display: inline-block;
                    background: #2563eb;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #64748b;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 AutoPro Elite</h1>
                    <p>Premium Automotive Solutions</p>
                </div>
                <div class="content">
                    <h2>Hello {customer_name},</h2>
                    <p>Thank you for your purchase! Your order has been confirmed and your invoice is ready.</p>
                    
                    <div class="order-details">
                        <h3>Order Summary</h3>
                        <div class="detail-row">
                            <span class="detail-label">Order ID:</span>
                            <span class="detail-value">#{order.id}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Bill Number:</span>
                            <span class="detail-value">{order.bill_number}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Order Type:</span>
                            <span class="detail-value">{order.get_order_type_display()}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Payment Method:</span>
                            <span class="detail-value">{(order.payment_method or 'COD').upper()}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Total Amount:</span>
                            <span class="detail-value total">₹{float(order.total_amount):,.2f}</span>
                        </div>
                    </div>
                    
                    <p>Your detailed invoice is attached to this email as a PDF file. You can also download it anytime from your account profile.</p>
                    
                    <p><strong>What's Next?</strong></p>
                    <ul>
                        <li>Your order is being processed</li>
                        <li>You'll receive updates via email and SMS</li>
                        <li>Track your order status in your account</li>
                    </ul>
                    
                    <p>If you have any questions or concerns, please don't hesitate to contact our support team.</p>
                    
                    <p>Best regards,<br><strong>AutoPro Elite Team</strong></p>
                </div>
                <div class="footer">
                    <p>AutoPro Elite | Premium Automotive Solutions</p>
                    <p>Email: support@autoproelite.com | Phone: +91-1234567890</p>
                    <p>Website: www.autoproelite.com</p>
                    <p style="font-size: 12px; margin-top: 15px;">
                        This is an automated email. Please do not reply directly to this message.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_message = f"""
        Hello {customer_name},
        
        Thank you for your purchase at AutoPro Elite!
        
        Order Details:
        - Order ID: #{order.id}
        - Bill Number: {order.bill_number}
        - Order Type: {order.get_order_type_display()}
        - Payment Method: {(order.payment_method or 'COD').upper()}
        - Total Amount: ₹{float(order.total_amount):,.2f}
        
        Your detailed invoice is attached to this email as a PDF file.
        
        If you have any questions, please contact us at support@autoproelite.com
        
        Best regards,
        AutoPro Elite Team
        """
        
        # Create email
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@autoproelite.com'),
            to=[customer_email],
        )
        
        # Attach HTML version
        email.content_subtype = "html"
        email.body = html_message
        
        # Attach PDF
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf_file:
                email.attach(
                    filename=f"Invoice_{order.bill_number}.pdf",
                    content=pdf_file.read(),
                    mimetype='application/pdf'
                )
        
        # Send email
        email.send(fail_silently=False)
        
        # Mark as sent
        order.bill_sent_email = True
        order.save(update_fields=['bill_sent_email'])
        
        print(f"E-bill sent successfully to {customer_email} for order #{order.id}")
        return True
        
    except Exception as e:
        print(f"Error sending e-bill email for order #{order.id}: {str(e)}")
        return False


def send_test_email(to_email):
    """Send a test email to verify email configuration"""
    try:
        subject = "Test Email from AutoPro Elite"
        message = "This is a test email to verify email configuration."
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@autoproelite.com'),
            to=[to_email],
        )
        
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        return False
