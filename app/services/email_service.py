import logging
from flask import current_app, render_template_string
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger('p2p.email')


class EmailService:
    @staticmethod
    def is_configured():
        cfg = current_app.config
        return bool(cfg.get('MAIL_SERVER') and cfg.get('MAIL_USERNAME'))

    @staticmethod
    def send_email(subject, recipients, html_body, text_body=None):
        if not recipients:
            return False

        if isinstance(recipients, str):
            recipients = [recipients]

        if not EmailService.is_configured():
            logger.info(
                f"[EmailService Simulation] SMTP not fully configured. Email subject: '{subject}' for {recipients} skipped safely."
            )
            return False

        try:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            msg = Message(subject=subject, recipients=recipients, sender=sender)
            msg.html = html_body
            if text_body:
                msg.body = text_body
            mail.send(msg)
            logger.info(f"Email '{subject}' sent successfully to {recipients}.")
            return True
        except Exception as e:
            logger.warning(f"Failed to send email '{subject}' to {recipients}: {type(e).__name__} - {e}")
            return False

    @classmethod
    def send_registration_confirmation(cls, user, team):
        subject = f"Registration Confirmed: {team.team_name} | Prompt to Product"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 30px; border-radius: 12px; border: 1px solid #1e293b;">
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="color: #3b82f6; margin: 0;">Prompt to Product</h2>
                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0;">AI Web Challenge | SSRS Group of Companies</p>
            </div>
            <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
                <h3 style="color: #00e5ff; margin-top: 0;">Congratulations, {user.full_name}!</h3>
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Your team has been successfully registered for the <strong>Prompt to Product – AI Web Challenge</strong>.
                </p>
                <div style="margin: 20px 0; padding: 15px; background: #1e293b; border-radius: 6px;">
                    <p style="margin: 4px 0; color: #94a3b8; font-size: 14px;">Team Registration ID:</p>
                    <p style="margin: 4px 0; font-size: 20px; font-weight: bold; color: #fbbf24; letter-spacing: 1px;">{team.registration_id}</p>
                    <p style="margin: 8px 0 4px; color: #94a3b8; font-size: 14px;">Team Name:</p>
                    <p style="margin: 4px 0; font-size: 16px; font-weight: bold; color: #ffffff;">{team.team_name}</p>
                </div>
                <h4 style="color: #ffffff; margin-bottom: 8px;">Next Steps:</h4>
                <ol style="color: #cbd5e1; line-height: 1.6; padding-left: 20px;">
                    <li>Join the official WhatsApp Community for live announcements.</li>
                    <li>Ensure all members have registered on the official Unstop opportunity page.</li>
                    <li>Access your leader dashboard to check the published problem statement.</li>
                </ol>
            </div>
            <p style="color: #64748b; font-size: 12px; text-align: center; margin-top: 25px;">
                Organized by SSRS Group of Companies. This is an automated email.
            </p>
        </div>
        """
        text = f"Hello {user.full_name},\nYour team '{team.team_name}' is registered with ID: {team.registration_id}.\nVisit your dashboard to view the problem statement."
        return cls.send_email(subject, user.email, html, text)

    @classmethod
    def send_password_reset_email(cls, user, reset_url):
        subject = "Password Reset Request | Prompt to Product"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 30px; border-radius: 12px; border: 1px solid #1e293b;">
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="color: #3b82f6; margin: 0;">Password Reset</h2>
                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0;">SSRS Group of Companies</p>
            </div>
            <p style="color: #cbd5e1; line-height: 1.6;">Hello {user.full_name},</p>
            <p style="color: #cbd5e1; line-height: 1.6;">
                We received a request to reset your password. Click the button below to choose a new password. This link is valid for 1 hour.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="display: inline-block; background: #3b82f6; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                    Reset My Password
                </a>
            </div>
            <p style="color: #94a3b8; font-size: 13px; line-height: 1.5;">
                If you did not request a password reset, please ignore this email or contact support if you suspect unauthorized access.
            </p>
        </div>
        """
        text = f"Hello {user.full_name},\nReset your password at: {reset_url}\nThis link expires in 1 hour."
        return cls.send_email(subject, user.email, html, text)

    @classmethod
    def send_submission_confirmation(cls, user, team, submission):
        subject = f"Submission Recorded: {team.team_name} | Prompt to Product"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 30px; border-radius: 12px; border: 1px solid #1e293b;">
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="color: #10b981; margin: 0;">Submission Received!</h2>
                <p style="color: #94a3b8; font-size: 14px; margin: 5px 0 0;">Prompt to Product – AI Web Challenge</p>
            </div>
            <div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Hello {user.full_name}, your deployed project link has been successfully submitted.
                </p>
                <div style="margin: 20px 0; padding: 15px; background: #1e293b; border-radius: 6px;">
                    <p style="margin: 4px 0; color: #94a3b8; font-size: 14px;">Submission ID:</p>
                    <p style="margin: 4px 0; font-size: 18px; font-weight: bold; color: #38bdf8;">{submission.submission_id}</p>
                    <p style="margin: 8px 0 4px; color: #94a3b8; font-size: 14px;">Deployed Website URL:</p>
                    <p style="margin: 4px 0; font-size: 14px; word-break: break-all; color: #00e5ff;">{submission.website_url}</p>
                </div>
                <div style="padding: 12px; background: rgba(245, 158, 11, 0.15); border-left: 4px solid #f59e0b; border-radius: 4px; margin: 20px 0;">
                    <strong style="color: #fbbf24;">Important Reminder:</strong>
                    <p style="color: #fef3c7; font-size: 13px; margin: 5px 0 0;">
                        Hackathon evaluation also requires submission on the official Unstop platform. If you have not done so, please complete your submission on Unstop before the deadline.
                    </p>
                </div>
            </div>
        </div>
        """
        text = f"Hello {user.full_name},\nYour submission {submission.submission_id} has been recorded with URL: {submission.website_url}.\nPlease also ensure you submit on Unstop!"
        return cls.send_email(subject, user.email, html, text)
