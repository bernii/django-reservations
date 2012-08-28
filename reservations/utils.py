from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings


def send_email(email_to, title, template, data):
    html_content = render_to_string(template, data)
    msg = EmailMessage(title, html_content, settings.EMAIL_FROM, [email_to])
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()
