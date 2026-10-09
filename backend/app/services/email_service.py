import logging
import smtplib
from email.message import EmailMessage
from typing import List
import uuid

from app.core.config import settings
from app.models.booking import Booking

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
        if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(f"SMTP not configured. Skipping email to {to_email}")
            logger.info(f"Email Content:\\nSubject: {subject}\\nBody:\\n{body}")
            return

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_USER
        msg['To'] = to_email

        if is_html:
            msg.set_content(body, subtype='html')
        else:
            msg.set_content(body)

        try:
            # We use synchronous smtplib in a quick wrapper because we don't have aiosmtplib.
            # In a real async environment, we'd use aiosmtplib or send this via a Celery queue.
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")

    @staticmethod
    async def send_booking_confirmation(user_email: str, pnr: str, bookings: List[Booking]):
        subject = f"Booking Confirmation - PNR: {pnr}"
        
        flight_details = ""
        total_price = 0
        currency = ""
        for b in bookings:
            flight = getattr(b, "flight", None)
            if flight:
                flight_details += f"<li>Flight {flight.flight_number}: {flight.origin} to {flight.destination} at {flight.departure_datetime}</li>"
            total_price += b.total_price
            currency = b.currency

        html_body = f"""
        <html>
        <body>
            <h2>Booking Confirmation</h2>
            <p>Thank you for booking with us. Your booking reference (PNR) is: <strong>{pnr}</strong></p>
            <h3>Itinerary Details:</h3>
            <ul>
                {flight_details}
            </ul>
            <p><strong>Total Price:</strong> {total_price} {currency}</p>
        </body>
        </html>
        """
        await EmailService.send_email(user_email, subject, html_body, is_html=True)

    @staticmethod
    async def send_cancellation_receipt(user_email: str, pnr: str, refund_amount: float, credit_amount: float):
        subject = f"Cancellation Receipt - PNR: {pnr}"
        html_body = f"""
        <html>
        <body>
            <h2>Booking Cancellation</h2>
            <p>Your booking with PNR <strong>{pnr}</strong> has been cancelled.</p>
            <p>Refund Amount: {refund_amount}</p>
            <p>Travel Credit Issued: {credit_amount}</p>
        </body>
        </html>
        """
        await EmailService.send_email(user_email, subject, html_body, is_html=True)
