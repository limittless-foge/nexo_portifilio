import os
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexo_web.settings')
django.setup()

from core.models import Project

def seed_projects():
    projects = [
        {
            "title": "Every Events Booking System",
            "category": "Event Tech",
            "description": "A comprehensive concert and event booking platform featuring secure QR-based ticket verification and real-time seating management."
        },
        {
            "title": "AV ERP Mobile Application",
            "category": "Enterprise",
            "description": "A robust ERP solution designed for mobile-first workflows, managing inventory, employee shifts, and logistics for industrial clients."
        },
        {
            "title": "Global E-Commerce Platform",
            "category": "Web Dev",
            "description": "Scalable multi-vendor e-commerce engine with integrated payment gateways, dynamic analytics, and AI-driven recommendations."
        },
        {
            "title": "FinTech Trading Dashboard",
            "category": "FinTech",
            "description": "High-performance trading interface with real-time data visualization, predictive market analysis, and multi-currency support."
        },
        {
            "title": "AI Content Generation Engine",
            "category": "AI/ML",
            "description": "Enterprise-grade AI platform for automated content creation, natural language processing, and brand-consistent copy generation."
        },
        {
            "title": "Smart Delivery & Logistics App",
            "category": "Logistics",
            "description": "Real-time delivery tracking system with route optimization, driver dispatch, and automated customer notifications."
        }
    ]

    print("Starting database seeding...")
    for p_data in projects:
        project, created = Project.objects.get_or_create(
            title=p_data['title'],
            defaults={
                'category': p_data['category'],
                'description': p_data['description'],
                'image_url': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2426' # Placeholder
            }
        )
        if created:
            print(f"Created project: {project.title}")
        else:
            print(f"Project already exists: {project.title}")

    print("Seeding complete!")

if __name__ == "__main__":
    seed_projects()
