
import os
from flask import render_template
from flask_mail import Mail, Message as MailMessage
from models import Message, db
from email_validator import validate_email as _validate_email, EmailNotValidError
import logging

logger = logging.getLogger(__name__)
mail = Mail()

def storing_database(data: dict) -> None:
    """Validate input and store a contact message in the database.

    Raises:
        ValueError: If validation fails for any field.
        RuntimeError: If a database error occurs while saving.
    """
    # Required fields and basic max length constraints aligned with DB schema
    required_fields = {
        'user_name': 100,
        'email': 120,
        'subject': 200,
        'text': None,  # message body (no strict DB length, but must be non-empty)
    }

    # Presence and basic validation
    cleaned = {}
    for field, max_len in required_fields.items():
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        value = str(data.get(field, '')).strip()
        if not value:
            raise ValueError(f"Field '{field}' must not be empty")
        if max_len is not None and len(value) > max_len:
            raise ValueError(f"Field '{field}' exceeds maximum length of {max_len}")
        cleaned[field] = value

    # Robust email validation
    try:
        # Validate format; skip deliverability/MX checks to avoid network calls
        validated = _validate_email(cleaned['email'], check_deliverability=False)
        cleaned['email'] = validated.email  # use normalized form
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email address: {str(e)}")

    # Map 'text' to message body column
    new_message = Message(
        user_name=cleaned['user_name'],
        email=cleaned['email'],
        subject=cleaned['subject'],
        message=cleaned['text'],
    )


    try:
        db.session.add(new_message)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Failed to store contact message: %s", exc)
        raise RuntimeError("Failed to save message. Please try again later.")

def send_email(subject, recipients, template, **kwargs):
    """Send an email notification using a template."""
    msg = MailMessage(subject, recipients=recipients)
    msg.html = render_template(template, **kwargs)
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")