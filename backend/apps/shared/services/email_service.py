"""
Email notification service for FLIPPY - inspired by the original FlippyBot email functionality.
"""
import os
from typing import List, Dict, Any, Optional
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications about new listings."""
    
    def __init__(self):
        """Initialize the email service with SendGrid configuration."""
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', None)
        self.to_email = getattr(settings, 'SENDGRID_TO_EMAIL', None)
        
        # Log configuration status (production-friendly)
        logger.info(f"Email service initialized - API key configured: {bool(self.api_key)}")
        
        if not all([self.api_key, self.from_email, self.to_email]):
            missing = []
            if not self.api_key: missing.append("SENDGRID_API_KEY")
            if not self.from_email: missing.append("SENDGRID_FROM_EMAIL")
            if not self.to_email: missing.append("SENDGRID_TO_EMAIL")
            logger.warning(f"SendGrid configuration incomplete. Missing: {', '.join(missing)}. Email notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self.client = SendGridAPIClient(self.api_key)
    
    def send_watchlist_notification(self, watchlist_items: List[Dict[str, Any]]) -> bool:
        """
        Send email notification for new watchlist items.
        
        Args:
            watchlist_items: List of dictionaries containing listing information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not enabled. Skipping notification.")
            return False
            
        if not watchlist_items:
            logger.info("No watchlist items to send.")
            return True
            
        try:
            # Group items by scanner for better organization
            scanner_groups = self._group_items_by_scanner(watchlist_items)
            
            # Generate email content
            html_content = self._generate_html_content(scanner_groups)
            text_content = self._generate_text_content(scanner_groups)
            
            # Create and send the email
            message = Mail(
                from_email=self.from_email,
                to_emails=self.to_email,
                subject=f'FLIPPY WATCHLIST: {len(watchlist_items)} New Listing(s) Found',
                plain_text_content=text_content,
                html_content=html_content
            )
            
            # Sandbox mode disabled - emails will be sent for real
            # Make sure your sender email is verified in SendGrid dashboard
            
            response = self.client.send(message)
            
            logger.info(f"Email notification sent - Status: {response.status_code}")
            
            if response.status_code in [200, 202]:
                logger.info(f"Successfully sent email notification for {len(watchlist_items)} items.")
                return True
            else:
                logger.error(f"Failed to send email. Status code: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _group_items_by_scanner(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group watchlist items by scanner for better email organization."""
        scanner_groups = {}
        for item in items:
            scanner = item.get('scanner', 'Unknown Scanner')
            if scanner not in scanner_groups:
                scanner_groups[scanner] = []
            scanner_groups[scanner].append(item)
        return scanner_groups
    
    def _generate_html_content(self, scanner_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate HTML email content based on the original FlippyBot format."""
        # CSS styles for consistent table formatting
        table_style = (
            "border-collapse: collapse; "
            "table-layout: fixed; "
            "width: 100%; "
            "margin-bottom: 20px;"
        )
        
        img_col_style = "width: 150px; word-wrap: break-word; white-space: normal; padding: 8px; border: 1px solid #ddd;"
        title_col_style = "width: 250px; word-wrap: break-word; white-space: normal; padding: 8px; border: 1px solid #ddd;"
        location_col_style = "width: 200px; word-wrap: break-word; white-space: normal; padding: 8px; border: 1px solid #ddd;"
        price_col_style = "width: 100px; word-wrap: break-word; white-space: normal; text-align: right; padding: 8px; border: 1px solid #ddd;"
        link_col_style = "width: 100px; word-wrap: break-word; white-space: normal; padding: 8px; border: 1px solid #ddd;"
        
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h2 { color: #2c3e50; }
                h3 { color: #34495e; margin-top: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th { background-color: #f8f9fa; font-weight: bold; }
                img { max-width: 150px; max-height: 150px; object-fit: cover; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h2>🔍 FLIPPY: New Listings Found</h2>
        """
        
        for scanner, items in scanner_groups.items():
            # Add scanner section header
            html_content += f"<h3>📍 Scanner: {scanner}</h3>"
            
            # Create table for this scanner's items
            html_content += f"""
            <table style="{table_style}">
                <tr>
                    <th style="{img_col_style}">Image</th>
                    <th style="{title_col_style}">Title</th>
                    <th style="{location_col_style}">Location</th>
                    <th style="{price_col_style}">Price</th>
                    <th style="{link_col_style}">Link</th>
                </tr>
            """
            
            # Add rows for each item
            for item in items:
                title = item.get('title', 'No title')
                location = item.get('location', 'No location')
                price = item.get('price', 'No price')
                url = item.get('url', '#')
                img_url = item.get('img', '')
                
                # Clean up data for display
                title = self._clean_html_text(title)
                location = self._clean_html_text(location)
                price = self._clean_html_text(price)
                
                html_content += f"""
                <tr>
                    <td style="{img_col_style}">
                        {f'<img src="{img_url}" alt="{title}" style="max-width:150px; max-height:150px;"/>' if img_url else 'No image'}
                    </td>
                    <td style="{title_col_style}">{title}</td>
                    <td style="{location_col_style}">{location}</td>
                    <td style="{price_col_style}"><strong>{price}</strong></td>
                    <td style="{link_col_style}"><a href="{url}" target="_blank">View Listing</a></td>
                </tr>
                """
            
            html_content += "</table>"
        
        html_content += """
            <hr style="margin: 20px 0;">
            <p style="color: #7f8c8d; font-size: 12px;">
                This email was sent by FLIPPY - Your Marketplace Deal Scanner<br>
                Found a great deal? Act fast - good deals don't last long!
            </p>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_text_content(self, scanner_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate plain text email content."""
        text_content = "FLIPPY: New Listings Found\n" + "="*40 + "\n\n"
        
        for scanner, items in scanner_groups.items():
            text_content += f"Scanner: {scanner}\n" + "-"*30 + "\n"
            
            for item in items:
                title = item.get('title', 'No title')
                location = item.get('location', 'No location')
                price = item.get('price', 'No price')
                url = item.get('url', '#')
                
                text_content += f"""
Title: {title}
Location: {location}
Price: {price}
Link: {url}

"""
            text_content += "\n"
        
        text_content += "\n" + "="*40
        text_content += "\nThis email was sent by FLIPPY - Your Marketplace Deal Scanner"
        text_content += "\nFound a great deal? Act fast - good deals don't last long!"
        
        return text_content
    
    def _clean_html_text(self, text: str) -> str:
        """Clean text for HTML display."""
        if not text:
            return ""
        return str(text).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
    
    def send_deep_analysis_notification(
        self, 
        notify_items: List[Dict[str, Any]], 
        recipient_emails: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification for AI deep analysis NOTIFY recommendations.
        
        Args:
            notify_items: List of dictionaries containing analyzed listing information
                         with AI recommendations and summaries
            recipient_emails: Optional list of recipient email addresses. If not provided,
                            uses the default from environment settings.
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not enabled. Skipping deep analysis notification.")
            return False
            
        if not notify_items:
            logger.info("No NOTIFY items to send.")
            return True
        
        # Determine recipient(s) - filter out empty values
        recipients = [email for email in (recipient_emails or []) if email]
        if not recipients:
            logger.warning("No recipient emails provided. Falling back to default.")
            recipients = [self.to_email] if self.to_email else []
        
        if not recipients:
            logger.error("No valid recipient emails. Cannot send notification.")
            return False
            
        try:
            # Generate email content with AI analysis details
            html_content = self._generate_deep_analysis_html(notify_items)
            text_content = self._generate_deep_analysis_text(notify_items)
            
            # Send ONE email to ALL recipients at once
            # SendGrid accepts a list of emails in to_emails
            message = Mail(
                from_email=self.from_email,
                to_emails=recipients,  # All recipients on one email
                subject=f'🎯 FLIPPY AI ALERT: {len(notify_items)} Deal(s) Found!',
                plain_text_content=text_content,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                logger.info(f"Deep analysis notification sent to {len(recipients)} recipient(s): {', '.join(recipients)} - Status: {response.status_code}")
                return True
            else:
                logger.error(f"Failed to send email to {recipients}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending deep analysis notification: {e}")
            return False
    
    def _generate_deep_analysis_html(self, notify_items: List[Dict[str, Any]]) -> str:
        """Generate HTML email content for deep analysis results."""
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }
                .header h1 { margin: 0; font-size: 24px; }
                .header p { margin: 5px 0 0 0; opacity: 0.9; }
                .listing-card { background: white; border-radius: 10px; margin: 15px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
                .listing-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #eee; }
                .listing-header .confidence { float: right; background: #28a745; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
                .listing-header .scanner { color: #6c757d; font-size: 12px; }
                .listing-body { display: flex; padding: 15px; }
                .listing-image { width: 150px; height: 150px; object-fit: cover; border-radius: 8px; margin-right: 15px; }
                .listing-image-placeholder { width: 150px; height: 150px; background: #eee; border-radius: 8px; margin-right: 15px; display: flex; align-items: center; justify-content: center; color: #999; }
                .listing-details { flex: 1; }
                .listing-title { font-size: 18px; font-weight: bold; color: #333; margin: 0 0 10px 0; }
                .listing-price { font-size: 24px; font-weight: bold; color: #28a745; margin: 0 0 10px 0; }
                .listing-location { color: #6c757d; font-size: 14px; margin: 0 0 10px 0; }
                .ai-summary { background: #e8f4fd; border-left: 4px solid #007bff; padding: 10px; margin: 10px 0; border-radius: 0 5px 5px 0; }
                .ai-summary-label { color: #007bff; font-weight: bold; font-size: 12px; margin-bottom: 5px; }
                .ai-summary-text { color: #333; font-size: 14px; margin: 0; }
                .analysis-details { background: #f8f9fa; padding: 15px; border-top: 1px solid #eee; }
                .analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
                .analysis-item { font-size: 13px; }
                .analysis-item .label { color: #6c757d; }
                .analysis-item .value { color: #333; font-weight: 500; }
                .cta-button { display: inline-block; background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; }
                .cta-button:hover { background: #0056b3; }
                .footer { text-align: center; padding: 20px; color: #6c757d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 FLIPPY AI Deal Alert</h1>
                    <p>Found """ + str(len(notify_items)) + """ listing(s) worth checking out!</p>
                </div>
        """
        
        for item in notify_items:
            title = self._clean_html_text(item.get('title', 'No title'))
            price = self._clean_html_text(item.get('price', 'No price'))
            location = self._clean_html_text(item.get('location', 'No location'))
            url = item.get('url', '#')
            img_url = item.get('img', '')
            confidence = item.get('confidence', 0)
            summary = self._clean_html_text(item.get('summary', 'Great deal found!'))
            scanner = self._clean_html_text(item.get('scanner', 'Scanner'))
            analysis = item.get('analysis', {})
            
            # Extract analysis details
            match_tier = analysis.get('match_tier', 'Unknown')
            ski_personality = analysis.get('ski_personality', '')
            use_case = analysis.get('use_case_flag', '')
            item_id = analysis.get('item_identification', {})
            brand = item_id.get('brand', '')
            model = item_id.get('model', '')
            size = item_id.get('size', '')
            condition = item_id.get('condition', '')
            value_assessment = analysis.get('value_assessment', {})
            estimated_value = value_assessment.get('estimated_value', '')
            savings = value_assessment.get('savings_percent', 0)
            
            # Confidence badge color
            conf_color = '#28a745' if confidence >= 80 else '#ffc107' if confidence >= 60 else '#dc3545'
            
            html_content += f"""
                <div class="listing-card">
                    <div class="listing-header">
                        <span class="confidence" style="background: {conf_color};">{confidence}% Confidence</span>
                        <div class="scanner">📍 {scanner}</div>
                    </div>
                    <div class="listing-body">
                        {f'<img class="listing-image" src="{img_url}" alt="{title}"/>' if img_url else '<div class="listing-image-placeholder">No Image</div>'}
                        <div class="listing-details">
                            <h3 class="listing-title">{title}</h3>
                            <p class="listing-price">{price}</p>
                            <p class="listing-location">📍 {location}</p>
                            <div class="ai-summary">
                                <div class="ai-summary-label">🤖 AI Analysis:</div>
                                <p class="ai-summary-text">{summary}</p>
                            </div>
                            <a href="{url}" class="cta-button" target="_blank">View Listing →</a>
                        </div>
                    </div>
                    <div class="analysis-details">
                        <div class="analysis-grid">
                            <div class="analysis-item"><span class="label">Tier:</span> <span class="value">{match_tier}</span></div>
                            <div class="analysis-item"><span class="label">Est. Value:</span> <span class="value">{estimated_value}</span></div>
                            <div class="analysis-item"><span class="label">Brand/Model:</span> <span class="value">{brand} {model}</span></div>
                            <div class="analysis-item"><span class="label">Size:</span> <span class="value">{size}</span></div>
                            <div class="analysis-item"><span class="label">Condition:</span> <span class="value">{condition}</span></div>
                            <div class="analysis-item"><span class="label">Savings:</span> <span class="value">{savings}%</span></div>
                            {f'<div class="analysis-item"><span class="label">Personality:</span> <span class="value">{ski_personality}</span></div>' if ski_personality else ''}
                            {f'<div class="analysis-item"><span class="label">Use Case:</span> <span class="value">{use_case}</span></div>' if use_case else ''}
                        </div>
                    </div>
                </div>
            """
        
        html_content += """
                <div class="footer">
                    <p>This alert was sent by FLIPPY - AI-Powered Marketplace Scanner</p>
                    <p>🚀 Act fast - good deals don't last long!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_deep_analysis_text(self, notify_items: List[Dict[str, Any]]) -> str:
        """Generate plain text email content for deep analysis results."""
        text_content = "🎯 FLIPPY AI DEAL ALERT\n" + "="*50 + "\n"
        text_content += f"Found {len(notify_items)} listing(s) worth checking out!\n\n"
        
        for i, item in enumerate(notify_items, 1):
            title = item.get('title', 'No title')
            price = item.get('price', 'No price')
            location = item.get('location', 'No location')
            url = item.get('url', '#')
            confidence = item.get('confidence', 0)
            summary = item.get('summary', 'Great deal found!')
            scanner = item.get('scanner', 'Scanner')
            analysis = item.get('analysis', {})
            
            match_tier = analysis.get('match_tier', 'Unknown')
            value_assessment = analysis.get('value_assessment', {})
            estimated_value = value_assessment.get('estimated_value', '')
            
            text_content += f"""
DEAL #{i} - {confidence}% Confidence
{"-"*40}
Title: {title}
Price: {price}
Location: {location}
Scanner: {scanner}
Tier: {match_tier}
Est. Value: {estimated_value}

🤖 AI Says: {summary}

View: {url}

"""
        
        text_content += "="*50
        text_content += "\nThis alert was sent by FLIPPY - AI-Powered Marketplace Scanner"
        text_content += "\n🚀 Act fast - good deals don't last long!"
        
        return text_content
    
    def test_email_configuration(self) -> bool:
        """
        Test the email configuration by sending a test email.
        
        Returns:
            bool: True if test email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.error("Email service not enabled. Cannot send test email.")
            return False
        
        try:
            test_message = Mail(
                from_email=self.from_email,
                to_emails=self.to_email,
                subject='FLIPPY: Email Configuration Test',
                plain_text_content='This is a test email from FLIPPY to verify email configuration.',
                html_content='<p>This is a test email from <strong>FLIPPY</strong> to verify email configuration.</p>'
            )
            
            # Sandbox mode disabled - emails will be sent for real
            # Make sure your sender email is verified in SendGrid dashboard
            
            response = self.client.send(test_message)
            
            logger.info(f"Test email sent - Status: {response.status_code}")
            
            if response.status_code in [200, 202]:
                logger.info("Test email sent successfully.")
                return True
            else:
                logger.error(f"Failed to send test email. Status code: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
