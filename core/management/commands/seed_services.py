import os
from django.core.management.base import BaseCommand
from core.models import ServiceCategory, SubService

class Command(BaseCommand):
    help = "Seeds the database with 7 core domains and 70+ sub-services."

    def handle(self, *args, **options):
        self.stdout.write("Seeding core service categories and sub-services...")

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
                    ("Presentation slide design", "Design professional slide decks in PowerPoint, Google Slides, Canva."),
                    ("Book covers & eBook design", "Captivating cover designs for print and digital publications."),
                    ("Resume/CV design", "Professional, high-impact resume and CV layouts."),
                    ("Letterheads & company profiles", "Official corporate stationery, branded profiles, and business layouts."),
                    ("Posters and flyers", "Eye-catching promotional flyers and poster prints."),
                    ("Brochures & leaflets", "Multi-page folded brochures and informative leaflets."),
                    ("Certificates & awards", "Formal recognition certificates and custom award templates."),
                    ("Menu design", "Structured food, beverage, or service menu cards."),
                    ("Business cards", "Sleek and memorable business cards for professional networking."),
                    ("Stickers & digital artwork", "Branded sticker assets and custom vector digital designs.")
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
                    ("Article and blog writing", "Deeply researched articles and blog posts tailored to your brand voice."),
                    ("Website content writing", "Professional landing page content and main site copy."),
                    ("Copywriting", "High-converting ad copy, sales copy, and product descriptions."),
                    ("Scriptwriting", "Engaging video scripts for YouTube, podcasts, or short video clips."),
                    ("Speech writing", "Tailored speeches and addresses for events and corporate presentations."),
                    ("Story writing & creative fiction", "Custom creative writing, fictional stories, and narrative drafts."),
                    ("Technical writing", "Clear software guides, user manuals, and technical documentation."),
                    ("Proposal & Grant writing", "Persuasive funding proposals, business grants, and pitches."),
                    ("Editing & proofreading", "Thorough grammar correction, syntax polishing, and style adjustments."),
                    ("Rewriting & paraphrasing", "Fresh adaptations of existing articles or text to bypass duplicate flags.")
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
                    ("Thesis & dissertation writing", "Ethical guided support, structuring, and research assistance for academic papers."),
                    ("Academic editing & formatting", "Comprehensive formatting matching APA, MLA, Chicago, or Vancouver guidelines."),
                    ("Research summaries & abstracts", "Concise summaries and abstracts of lengthy studies or journals."),
                    ("Referencing & citation management", "Accurate citation insertion, reference listing, and bibliography cleanup."),
                    ("Research proposals", "Structured proposals outlining hypotheses, methods, and literature gaps."),
                    ("Plagiarism checking & reduction", "Originality reports and editing to reduce text duplication indices."),
                    ("PowerPoint presentations for research defense", "Professional slides designed for thesis defense presentations."),
                    ("Research publication preparation", "Refining articles to meet academic publisher submission requirements."),
                    ("Systematic reviews & scoping reviews", "Methodical synthesis and analysis of literature for specific study topics."),
                    ("Academic poster design", "Large-format visual posters for research conferences and symposiums.")
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
                    ("Data entry", "Fast and accurate data entry across spreadsheets and CRM portals."),
                    ("Basic programming", "Custom script creation using Python, R, or SQL query development."),
                    ("Automation scripts", "Automating repetitive workflows, web scraping, and API sync processes."),
                    ("Data cleaning", "Formatting raw lists, removing duplicates, and structuring text fields."),
                    ("Excel spreadsheet creation", "Creating formulas, pivot tables, and custom templates in Microsoft Excel."),
                    ("Database management", "Relational database structuring, migration scripts, and schema optimizations."),
                    ("Data collection & survey design development", "Creating surveys, questionnaires, and structuring data capture methods."),
                    ("Questionnaire development", "Drafting research questionnaires with sound psychological/demographic structures."),
                    ("Data analysis", "Statistical analysis using SPSS, Stata, Python, or Excel macros."),
                    ("Statistical interpretation", "Writing explanatory narratives based on complex statistical analysis reports.")
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
                    ("Website design", "Sleek website construction in WordPress, Wix, or custom HTML/CSS."),
                    ("UI/UX design", "Figma wireframes and interactive prototypes for desktop or mobile apps."),
                    ("SEO optimization", "On-page, technical, and keywords optimization to boost search ranking."),
                    ("Landing page creation", "High-converting, responsive single-page layouts for campaigns."),
                    ("Domain & hosting setup", "Domain registration, DNS configurations, and hosting server setups."),
                    ("Website testing & debugging", "Comprehensive QA testing, cross-browser audits, and bug fixes."),
                    ("Social media management", "Content calendars, caption drafting, and platform post scheduling."),
                    ("Digital ad design", "Designing promotional visual creatives for Facebook, Instagram, or Google Ads."),
                    ("Email marketing campaigns", "Newsletter layouts, autoresponder setups, and list sequence copies."),
                    ("Content strategy development", "Comprehensive content roadmaps based on target audience analysis.")
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
                    ("Business plan writing", "Formal business plans containing market analysis and financial sections."),
                    ("Pitch deck creation", "Polished pitch decks tailored to prospective investors or partners."),
                    ("Market research", "Comprehensive market trend summaries, demographic analyses, and niche research."),
                    ("Competitor & SWOT analysis", "In-depth competitor audits and SWOT analysis matrices."),
                    ("Business reports", "Formal corporate reports, performance briefs, and executive summaries."),
                    ("Email & calendar management", "Assisting with inbox sorting, filter management, and meeting scheduling."),
                    ("Meeting notes & minutes", "Documenting minutes, action points, and summaries from virtual meetings."),
                    ("Appointment booking & travel arrangements", "Managing flight bookings, hotel reservations, and calendar events."),
                    ("Financial analysis", "Assisting with basic financial statements, models, and cost analyses."),
                    ("Customer service support", "Responding to client queries, email desk management, and support services.")
                ]
            },
            {
                'code': 'MULTIMEDIA',
                'title': 'Education & Multimedia',
                'description': 'Online tutoring, course design, e-learning content, and media production.',
                'icon_class': 'fas fa-graduation-cap',
                'header_image': 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?q=80&w=2070',
                'order': 7,
                'is_external_link': True,
                'external_url': 'https://wisdo-tower.com/education/',
                'sub_services': [
                    ("Online tutoring", "Interactive, personalized virtual tutoring sessions across subjects."),
                    ("Course creation & eLearning content design", "Designing structured online courses, syllabus maps, and slides."),
                    ("Lesson plan development", "Drafting step-by-step educational lesson guides for schools or tutors."),
                    ("Quiz & exam creation", "Constructing testing forms, diagnostic quizzes, and exam structures."),
                    ("Online form creation", "Designing functional customer intake forms, surveys, or feedback sheets."),
                    ("eBook formatting", "Converting raw text manuscript into polished EPUB or print formats."),
                    ("PDF editing & document conversion", "Editing existing PDFs, forms layout conversion, or OCR conversion."),
                    ("Audio transcription", "Accurately converting podcasts, lectures, or interviews to clean transcripts."),
                    ("Video editing & subtitles", "Polishing video reels, adding captions, and dynamic subtitles."),
                    ("Voiceover recording", "High-quality vocal recordings for explainer videos, ads, or modules.")
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

        self.stdout.write(self.style.SUCCESS("Successfully seeded all 7 domains and 70+ sub-services!"))
