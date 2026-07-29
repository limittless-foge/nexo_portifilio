import os
from django.core.management.base import BaseCommand
from core.models import ServiceCategory, SubService

class Command(BaseCommand):
    help = "Seeds the database with 7 core WISDOM TOWER domains and sub-services."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Wisdom Tower service categories and sub-services...")

        # 1. Clear old data to prevent duplication
        SubService.objects.all().delete()
        ServiceCategory.objects.all().delete()

        domains_data = [
            {
                'code': 'DESIGN',
                'title': 'Graphic & Print Design',
                'description': 'Visual identity crafted for print and digital impact.',
                'icon_class': 'fas fa-palette',
                'header_image': 'https://images.unsplash.com/photo-1626785774625-ddcddc3445e9?q=80&w=2071',
                'order': 1,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Visual communication & brand identity", "Cohesive visual styles, logos, and corporate brand kits."),
                    ("Presentation slide design (PowerPoint, Google Slides, Canva)", "Dynamic presentation slides and investor pitch decks."),
                    ("Book covers & eBook design", "Captivating cover designs and eBook layouts."),
                    ("Resume/CV design", "Job-winning, professional resume and CV templates."),
                    ("Letterheads & company profiles", "Corporate letters, business documents, and company profiles."),
                    ("Posters, flyers, brochures & leaflets", "High-quality promotional leaflets, brochures, and poster prints."),
                    ("Certificates, awards & menu design", "Formal recognition certificates and custom menu designs."),
                    ("Business cards, stickers & digital artwork", "Networking cards, custom stickers, and digital illustrations.")
                ]
            },
            {
                'code': 'WRITING',
                'title': 'Writing & Editorial',
                'description': 'Words that persuade, inform, and convert.',
                'icon_class': 'fas fa-pen-nib',
                'header_image': 'https://images.unsplash.com/photo-1455390582262-044cdead277a?q=80&w=2073',
                'order': 2,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Article and blog writing", "SEO-optimized articles and engaging blog posts."),
                    ("Website content writing", "Compelling web copy including homepage, landing page, and about sections."),
                    ("Copywriting (ads, product descriptions)", "High-converting ad copy, sales copy, and product descriptions."),
                    ("Scriptwriting (YouTube, podcasts, short films)", "Narrative and instructional scripts designed for engagement and flow."),
                    ("Speech writing & creative fiction stories", "Powerful keynote speeches and custom narrative stories."),
                    ("Technical writing, proposal & grant writing", "Technical manuals, grant writing, and business proposals."),
                    ("Editing, proofreading, rewriting & paraphrasing", "Thorough grammar correction and style polishing.")
                ]
            },
            {
                'code': 'ACADEMIC',
                'title': 'Academic & Research Support',
                'description': 'Rigorous research and academic formatting.',
                'icon_class': 'fas fa-graduation-cap',
                'header_image': 'https://images.unsplash.com/photo-1532012197267-da84d127e765?q=80&w=2074',
                'order': 3,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Thesis & dissertation writing support", "Ethical structure support, feedback, and editing assistance."),
                    ("Academic editing & formatting (APA, MLA, Chicago, Vancouver)", "Precision formatting according to standard styles."),
                    ("Research summaries, proposals & abstracts", "Synthesizing lengthy studies and drafting abstracts."),
                    ("Referencing & citation management", "Accurate citation catalogs and bibliography cleanup."),
                    ("Plagiarism checking & reduction", "Originality scans and paraphrasing to reduce similarity index."),
                    ("PowerPoint presentations for research defense", "Scientific slides optimized for thesis defenses."),
                    ("Research publication preparation", "Refining research papers for academic journal submission."),
                    ("Systematic reviews, scoping reviews & academic poster design", "Synthesis of literature and conference poster layouts.")
                ]
            },
            {
                'code': 'DATA_TECH',
                'title': 'Data & Tech Solutions',
                'description': 'Custom web software, APIs, and analytics engineering.',
                'icon_class': 'fas fa-database',
                'header_image': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070',
                'order': 4,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Data entry & cleaning", "Fast database input and cleaning/standardizing records."),
                    ("Basic programming (Python, R, SQL)", "Custom code scripts, automated commands, and database querying."),
                    ("Automation scripts", "Process automation, web scraping, and API integrations."),
                    ("Excel spreadsheet creation & database management", "Complex pivot tables, databases, and automated spreadsheets."),
                    ("Data collection, questionnaire development & survey design", "Gathering data inputs and drafting survey questionnaires."),
                    ("Data analysis & statistical interpretation (SPSS, Stata, R, Excel)", "Processing statistical data and writing narratives.")
                ]
            },
            {
                'code': 'MARKETING',
                'title': 'Web & Digital Marketing',
                'description': 'Multi-channel growth, campaigns, and audience engagement.',
                'icon_class': 'fas fa-bullhorn',
                'header_image': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2426',
                'order': 5,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Website design (WordPress, Wix, HTML/CSS)", "Responsive, modern websites built for business growth."),
                    ("UI/UX design & landing page creation", "Figma layouts, wireframes, and optimized landing pages."),
                    ("SEO optimization, domain & hosting setup", "Boosting search rank, hosting server, and domain configurations."),
                    ("Website testing & debugging", "QA audits, user experience checks, and code debugging."),
                    ("Social media management & content strategy", "Content planning, captions, and platform post calendars."),
                    ("Digital ad design (Facebook, Google Ads)", "Creative graphic ads to maximize ad conversions."),
                    ("Email marketing campaigns", "Newsletter layouts, sequences, and autoresponder setups.")
                ]
            },
            {
                'code': 'BUSINESS',
                'title': 'Business Strategy & Admin',
                'description': 'Pitch decks, financial modeling, and administrative support.',
                'icon_class': 'fas fa-chart-line',
                'header_image': 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?q=80&w=2071',
                'order': 6,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Business plan writing & pitch deck creation", "Formal business plans and raise-ready presentation decks."),
                    ("Market research, competitor & SWOT analysis", "In-depth research on competitors, SWOT matrices, and niches."),
                    ("Business reports & financial analysis", "Financial statements, models, and formal company reports."),
                    ("Email, calendar & appointment management", "Inbox sorting, virtual calendars, and appointment schedules."),
                    ("Meeting notes, minutes & customer service support", "Documenting call notes and resolving customer queries.")
                ]
            },
            {
                'code': 'MULTIMEDIA',
                'title': 'Education & Multimedia',
                'description': 'Online tutoring, course design, e-learning content, and media production.',
                'icon_class': 'fas fa-graduation-cap',
                'header_image': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?q=80&w=2070',
                'order': 7,
                'is_external_link': False,
                'external_url': None,
                'sub_services': [
                    ("Online tutoring & lesson plan development", "Personalized tutoring sessions and syllabus creation."),
                    ("Course creation & eLearning content design", "Design online courses, slide templates, and modules."),
                    ("Quiz, exam & online form creation", "Diagnostic testing sheets and intake/feedback forms."),
                    ("eBook formatting, PDF editing & document conversion", "EPUB/print conversion, OCR, and editing layout text."),
                    ("Audio transcription, voiceover recording", "Vocal recordings and clean audio-to-text transcripts."),
                    ("Video editing & subtitles", "Cutting video reels and adding dynamic subtitle tracks.")
                ]
            }
        ]

        for domain in domains_data:
            category = ServiceCategory.objects.create(
                title=domain['title'],
                description=domain['description'],
                icon_class=domain['icon_class'],
                header_image=domain['header_image'],
                order=domain['order'],
                is_external_link=domain['is_external_link'],
                external_url=domain['external_url']
            )
            self.stdout.write(f"Created category: {category.title}")

            for sub_title, sub_desc in domain['sub_services']:
                sub_service = SubService.objects.create(
                    service_category=category,
                    category=domain['code'],
                    title=sub_title,
                    short_explanation=sub_desc
                )
                self.stdout.write(f"  -> Created sub-service: {sub_service.title}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded all 7 WISDOM TOWER domains!"))
