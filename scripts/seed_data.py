import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.content import ProblemStatement, FAQ, Announcement
from app.services.settings_service import SettingsService


def run_seed():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("Seeding Initial Application Data...")
        print("=" * 60)

        # 1. Site Settings
        SettingsService.seed_defaults()
        print("[OK] Site settings seeded.")

        # 2. Problem Statement
        existing_ps = ProblemStatement.query.first()
        if not existing_ps:
            ps = ProblemStatement(
                title="AI-Powered Intelligent Web Solution for Modern Digital Workflows",
                description="Harness the power of Artificial Intelligence and advanced prompt engineering to design and build an innovative, high-performance web application that solves critical real-world challenges.",
                objectives="""1. Develop a fully responsive, intuitive, and modern web application.
2. Leverage generative AI capabilities, prompt engineering, or intelligent workflows to enhance user value.
3. Deliver a robust frontend and backend architecture adhering to modern web security best practices.
4. Deploy the solution to a reliable public hosting provider for real-time evaluation.""",
                requirements="""• Responsive layout compatible with smartphones, tablets, and laptops.
• Working core feature loop demonstrating intelligence or generative automation.
• Clean visual hierarchy, accessible UI components, and intuitive UX flows.
• Live deployment accessible through public HTTPS URL.
• No broken routes, non-functional buttons, or missing assets.""",
                guidelines="""• Open to individuals and teams of 1 to 4 members.
• All team members must be registered under their team leader.
• Use of AI coding assistants (ChatGPT, Claude, Gemini, GitHub Copilot) and prompt engineering is enthusiastically encouraged.
• Only public deployed website links are accepted as final submissions.
• Submissions must also be verified and completed on the official Unstop platform.""",
                evaluation_criteria="""1. Functionality & Execution (10 Marks): Smooth operation, absence of critical bugs, and complete end-to-end workflow.
2. Innovation & AI Integration (10 Marks): Creative application of prompt engineering and intelligent digital product concepts.
3. UI/UX Design & Responsiveness (10 Marks): Visual polish, clean typography, responsiveness, and premium aesthetics.
4. Real-World Impact (10 Marks): Practical relevance, problem clarity, and potential business or societal value.
5. Code Quality & Architecture (10 Marks): Clean code organization, maintainability, and security practices.
6. Deployment & Performance (10 Marks): Fast load times, reliable uptime, and valid SSL/HTTPS configuration.""",
                submission_instructions="""1. Deploy your web application to a public cloud hosting platform (such as Vercel, Netlify, Render, Railway, AWS, or GitHub Pages).
2. Enter your public website URL in the submission form at `/dashboard/submit`.
3. Provide a brief 1-2 paragraph description highlighting your solution's key features and AI workflow.
4. Click 'Submit Project' on your dashboard.
5. Complete the corresponding submission step on the official Unstop challenge page.""",
                status='published',
                version=1,
                published_at=datetime.utcnow()
            )
            db.session.add(ps)
            print("[OK] Published Problem Statement v1 created.")
        else:
            print("[INFO] Problem Statement already exists, skipping.")

        # 3. FAQs
        if FAQ.query.count() == 0:
            faq_data = [
                (
                    "What is Prompt to Product – AI Web Challenge?",
                    "Prompt to Product is a national-level online hackathon organized by SSRS Group of Companies. It challenges participants to turn innovative concepts into functional, deployed web applications using AI tools and prompt engineering.",
                    1
                ),
                (
                    "What is the permissible team size?",
                    "Teams can consist of 1 to 4 members (individual participants or teams up to 4). The team leader registers the team and manages submissions on behalf of all members.",
                    2
                ),
                (
                    "Is there any registration fee for the hackathon?",
                    "No! Participation is completely free for all eligible students and developers.",
                    3
                ),
                (
                    "Are AI tools and prompt engineering allowed?",
                    "Absolutely! The core theme of Prompt to Product is leveraging modern AI assistants and prompt engineering to accelerate development and build intelligent digital products.",
                    4
                ),
                (
                    "What kind of submissions are accepted?",
                    "Only deployed public website URLs (HTTP/HTTPS) are accepted. Do not upload ZIP files, source folders, or PDFs to the submission portal.",
                    5
                ),
                (
                    "Do I also need to register and submit on Unstop?",
                    "Yes. SSRS Group of Companies is hosting the challenge in association with Unstop. While this website manages your team account and official submission link, you must also register and submit through the official Unstop opportunity page.",
                    6
                ),
                (
                    "What are the prizes and recognition?",
                    "Certificates of Excellence will be awarded to the top 3 winning teams. Participation certificates are also available for eligible teams that submit a valid, functional project.",
                    7
                ),
            ]
            for q, a, order in faq_data:
                f = FAQ(question=q, answer=a, display_order=order, is_published=True)
                db.session.add(f)
            print("[OK] FAQs seeded.")
        else:
            print("[INFO] FAQs already present, skipping.")

        # 4. Announcements
        if Announcement.query.count() == 0:
            ann = Announcement(
                title="Prompt to Product – AI Web Challenge is Officially Live!",
                message="Welcome participants! Team registrations are now open and the official problem statement has been published. Read the guidelines carefully and join our WhatsApp community for live updates.",
                is_published=True,
                published_at=datetime.utcnow()
            )
            db.session.add(ann)
            print("[OK] Welcome Announcement created.")
        else:
            print("[INFO] Announcements already present, skipping.")

        db.session.commit()
        print("=" * 60)
        print("Database seed completed successfully!")
        print("=" * 60)


if __name__ == '__main__':
    run_seed()
