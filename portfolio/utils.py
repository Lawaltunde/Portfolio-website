
import os
from flask import render_template
from flask_mail import Mail, Message as MailMessage
from email_validator import validate_email as _validate_email, EmailNotValidError
import logging

logger = logging.getLogger(__name__)


mail = Mail()

def send_email(subject, recipients, template, **kwargs):
    """Send an email notification using a template."""
    msg = MailMessage(subject, recipients=recipients)
    msg.html = render_template(template, **kwargs)
    try:
        mail.send(msg)
    except Exception as e:
        logger.exception(f"Failed to send email: {e}")