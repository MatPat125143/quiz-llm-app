import logging
import os
from smtplib import SMTPException
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailService:

    def __init__(self):
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', 'quiz-llm-app@wp.pl')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Quiz LLM App')

    def send_password_reset_email(self, recipient_email, reset_code):
        subject = "Kod resetowania hasła - Quiz LLM App"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Resetowanie hasła</h2>
                    <p>Otrzymaliśmy prośbę o reset hasła do Twojego konta w Quiz LLM App.</p>
                    <p>Twój kod resetowania hasła:</p>
                    <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #4F46E5; letter-spacing: 4px;">{reset_code}</span>
                    </div>
                    <p><strong>Kod wygasa za 1 godzinę.</strong></p>
                    <p>Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość - Twoje hasło pozostanie bez zmian.</p>
                    <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
                    <p style="font-size: 12px; color: #6B7280;">
                        To jest automatyczna wiadomość z Quiz LLM App. Nie odpowiadaj na ten email.
                    </p>
                </div>
            </body>
        </html>
        """

        text_content = f"""
Resetowanie hasła - Quiz LLM App

Otrzymaliśmy prośbę o reset hasła do Twojego konta.

Twój kod resetowania hasła: {reset_code}

Kod wygasa za 1 godzinę.

Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość - Twoje hasło pozostanie bez zmian.
        """

        try:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=f"{self.from_name} <{self.from_email}>",
                recipient_list=[recipient_email],
                html_message=html_content,
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {recipient_email}")
            return True

        except (SMTPException, OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Failed to send password reset email to {recipient_email}: {e}")
            return False

    def send_welcome_email(self, recipient_email, username):
        subject = "Witamy w Quiz LLM App!"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Witamy w Quiz LLM App!</h2>
                    <p>Cześć {username},</p>
                    <p>Dziękujemy za rejestrację w Quiz LLM App. Cieszymy się, że do nas dołączyłeś!</p>
                    <p>Możesz teraz tworzyć i rozwiązywać quizy AI na dowolny temat.</p>
                    <p>Jeśli masz pytania, skontaktuj się z naszym zespołem wsparcia.</p>
                    <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
                    <p style="font-size: 12px; color: #6B7280;">
                        To jest automatyczna wiadomość z Quiz LLM App.
                    </p>
                </div>
            </body>
        </html>
        """

        text_content = f"""
Witamy w Quiz LLM App!

Cześć {username},

Dziękujemy za rejestrację w Quiz LLM App. Cieszymy się, że do nas dołączyłeś!

Możesz teraz tworzyć i rozwiązywać quizy AI na dowolny temat.

Jeśli masz pytania, skontaktuj się z naszym zespołem wsparcia.
        """

        try:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=f"{self.from_name} <{self.from_email}>",
                recipient_list=[recipient_email],
                html_message=html_content,
                fail_silently=False,
            )
            logger.info(f"Welcome email sent to {recipient_email}")
            return True

        except (SMTPException, OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Failed to send welcome email to {recipient_email}: {e}")
            return False


email_service = EmailService()
