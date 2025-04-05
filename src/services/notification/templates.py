import os
from pathlib import Path
import logging


logger = logging.getLogger(__name__)

# Fallback templates that will be used if file templates aren't available
FALLBACK_TEMPLATES = {
    "meeting_notification": """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-bottom: 3px solid #007bff;">
                <h2 style="color: #007bff; margin: 0;">New Meeting Logged</h2>
            </div>
            <div style="padding: 20px;">
                <p>A new meeting has been processed and logged to Google Sheets:</p>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <th style="text-align: left; padding: 8px; background-color: #f2f2f2; border: 1px solid #ddd;">Field</th>
                        <th style="text-align: left; padding: 8px; background-color: #f2f2f2; border: 1px solid #ddd;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Customer:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{customer_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Meeting Date:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{meeting_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Start Time:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{start_time}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>End Time:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{end_time}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Total Hours:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{total_hours}</td>
                    </tr>
                </table>
                
                <div style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #6c757d; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Notes:</h3>
                    <p>{notes}</p>
                </div>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #6c757d; font-size: 12px;">This is an automated notification from Voice-TimeLogger-Agent.</p>
            </div>
        </body>
        </html>
    """,
    "default": "<html><body><p>Meeting data from {customer_name} on {meeting_date}</p></body></html>"
}

def load_template(template_name):
    """
    Load a template from file.
    
    Args:
        template_name: Name of the template to load
        
    Returns:
        Template content as string
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_dir = Path(__file__).parent / "templates"
    template_path = template_dir / f"{template_name}.html"
    
    if not template_path.exists():
        logger.warning(f"Template file not found: {template_path}")
        if template_name in FALLBACK_TEMPLATES:
            logger.info(f"Using fallback template for: {template_name}")
            return FALLBACK_TEMPLATES[template_name]
        else:
            logger.warning(f"No fallback template for: {template_name}, using default")
            return FALLBACK_TEMPLATES["default"]
            
    try:
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading template file {template_path}: {str(e)}")
        # Use fallback template
        if template_name in FALLBACK_TEMPLATES:
            logger.info(f"Using fallback template for: {template_name}")
            return FALLBACK_TEMPLATES[template_name]
        else:
            logger.warning(f"No fallback template for: {template_name}, using default")
            return FALLBACK_TEMPLATES["default"]

def get_template(template_name):
    """
    Get a template by name with caching.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Template content as string
    """
    if not hasattr(get_template, "_templates"):
        get_template._templates = {}
    
    if template_name not in get_template._templates:
        get_template._templates[template_name] = load_template(template_name)
    
    return get_template._templates[template_name]