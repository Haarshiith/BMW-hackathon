#!/usr/bin/env python3
"""
Synthetic Data Generator for BMW Incident Reporting System

This script generates realistic incident data for testing the system.
It creates diverse, realistic scenarios across different departments with
varying severities, commodities, and solutions.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base, init_db
from app.models.lesson_learned import LessonLearned, SeverityLevel
from app.config import settings

# Database setup
DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Realistic data templates
DEPARTMENTS = [
    "engineering", "manufacturing", "sales", "quality", "it", "hr"
]

COMMODITIES = {
    "engineering": [
        "Engine Components", "Transmission Systems", "Brake Systems", "Suspension Parts",
        "Electrical Systems", "Fuel Systems", "Cooling Systems", "Exhaust Systems",
        "Steering Components", "Safety Systems", "Navigation Systems", "Climate Control"
    ],
    "manufacturing": [
        "Body Panels", "Interior Components", "Glass Components", "Seating Systems",
        "Dashboard Assemblies", "Door Handles", "Mirrors", "Lighting Systems",
        "Wiring Harnesses", "Fasteners", "Gaskets", "Seals"
    ],
    "quality": [
        "Paint Quality", "Surface Finish", "Dimensional Accuracy", "Material Properties",
        "Assembly Quality", "Functional Testing", "Durability Testing", "Safety Testing",
        "Performance Testing", "Environmental Testing", "Compliance Testing", "Reliability Testing"
    ],
    "it": [
        "Software Systems", "Hardware Infrastructure", "Network Systems", "Database Systems",
        "Security Systems", "Mobile Applications", "Web Applications", "Cloud Services",
        "Backup Systems", "Monitoring Systems", "Integration Systems", "User Support"
    ],
    "hr": [
        "Employee Relations", "Training Programs", "Performance Management", "Recruitment",
        "Benefits Administration", "Workplace Safety", "Compliance", "Policy Management",
        "Employee Development", "Compensation", "Workplace Culture", "Diversity & Inclusion"
    ],
    "sales": [
        "Customer Relations", "Sales Processes", "Pricing Strategy", "Market Analysis",
        "Lead Generation", "Sales Training", "Customer Support", "Sales Reporting",
        "Territory Management", "Product Knowledge", "Negotiation", "Sales Tools"
    ]
}

SUPPLIERS = [
    "Bosch Automotive", "Continental AG", "ZF Friedrichshafen", "Magna International",
    "Valeo", "Faurecia", "Lear Corporation", "Aptiv", "Denso Corporation", "Hyundai Mobis",
    "Bridgestone", "Michelin", "Goodyear", "Pirelli", "Schaeffler Group", "GKN Automotive",
    "BorgWarner", "Mahle", "Federal-Mogul", "Tenneco", "Johnson Controls", "Adient",
    "Autoliv", "Takata", "TRW Automotive", "Delphi Technologies", "Visteon", "Gentex",
    "Magna Steyr", "Valmet Automotive", "Bertrandt", "EDAG", "IAV", "FEV"
]

PART_NUMBERS = [
    "BMW-ENG-001", "BMW-TRN-002", "BMW-BRK-003", "BMW-SUS-004", "BMW-ELE-005",
    "BMW-FUL-006", "BMW-COO-007", "BMW-EXH-008", "BMW-STE-009", "BMW-SAF-010",
    "BMW-NAV-011", "BMW-CLI-012", "BMW-BOD-013", "BMW-INT-014", "BMW-GLA-015",
    "BMW-SEA-016", "BMW-DAS-017", "BMW-DOR-018", "BMW-MIR-019", "BMW-LIG-020",
    "BMW-WIR-021", "BMW-FAS-022", "BMW-GAS-023", "BMW-SEA-024", "BMW-PAI-025"
]

ERROR_LOCATIONS = [
    "Assembly Line Station 1", "Assembly Line Station 2", "Assembly Line Station 3",
    "Quality Control Station", "Final Inspection Area", "Testing Laboratory",
    "Packaging Area", "Shipping Dock", "Receiving Area", "Warehouse Storage",
    "Production Floor", "Clean Room", "Paint Shop", "Body Shop", "Trim Shop",
    "Engine Assembly", "Transmission Assembly", "Chassis Assembly", "Interior Assembly",
    "Electrical Testing", "Performance Testing", "Durability Testing", "Safety Testing"
]

REPORTER_NAMES = [
    "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis", "David Wilson",
    "Lisa Anderson", "Robert Taylor", "Jennifer Martinez", "Christopher Garcia",
    "Amanda Rodriguez", "James Lee", "Michelle White", "Daniel Harris", "Ashley Martin",
    "Matthew Thompson", "Jessica Garcia", "Andrew Martinez", "Stephanie Robinson",
    "Joshua Clark", "Nicole Rodriguez", "Kevin Lewis", "Samantha Walker", "Ryan Hall",
    "Brittany Allen", "Tyler Young", "Megan King", "Brandon Wright", "Rachel Lopez",
    "Justin Hill", "Lauren Scott", "Jacob Green", "Kayla Adams", "Nathan Baker",
    "Amber Gonzalez", "Zachary Nelson", "Danielle Carter", "Austin Mitchell",
    "Brianna Perez", "Caleb Roberts", "Taylor Turner", "Noah Phillips", "Morgan Campbell"
]

# Problem scenarios by department
PROBLEM_SCENARIOS = {
    "engineering": [
        "Engine knocking sound during cold start conditions",
        "Transmission slipping in 3rd and 4th gears under load",
        "Brake pedal feels spongy and requires excessive travel",
        "Suspension making clunking noise over bumps",
        "Electrical system showing intermittent power loss",
        "Fuel system experiencing pressure fluctuations",
        "Cooling system overheating under normal driving conditions",
        "Exhaust system producing excessive noise and vibration",
        "Steering wheel pulling to the right during acceleration",
        "Safety systems showing false positive warnings",
        "Navigation system losing GPS signal in urban areas",
        "Climate control not maintaining set temperature"
    ],
    "manufacturing": [
        "Body panel gaps exceeding tolerance specifications",
        "Interior trim pieces not fitting properly during assembly",
        "Glass components showing stress cracks after installation",
        "Seating systems failing comfort and durability tests",
        "Dashboard assembly showing misalignment issues",
        "Door handles requiring excessive force to operate",
        "Mirrors not maintaining position after adjustment",
        "Lighting systems showing inconsistent beam patterns",
        "Wiring harnesses failing continuity tests",
        "Fasteners not achieving proper torque specifications",
        "Gaskets showing signs of premature wear",
        "Seals not providing adequate weather protection"
    ],
    "quality": [
        "Paint showing orange peel texture on horizontal surfaces",
        "Surface finish not meeting gloss specifications",
        "Dimensional measurements outside acceptable tolerances",
        "Material properties failing stress test requirements",
        "Assembly quality not meeting visual standards",
        "Functional testing revealing performance degradation",
        "Durability testing showing premature component failure",
        "Safety testing revealing potential hazard conditions",
        "Performance testing showing efficiency below targets",
        "Environmental testing revealing corrosion issues",
        "Compliance testing failing regulatory requirements",
        "Reliability testing showing high failure rates"
    ],
    "it": [
        "Software systems experiencing frequent crashes",
        "Hardware infrastructure showing performance degradation",
        "Network systems experiencing connectivity issues",
        "Database systems showing slow query performance",
        "Security systems detecting potential breaches",
        "Mobile applications not functioning on certain devices",
        "Web applications showing user interface problems",
        "Cloud services experiencing availability issues",
        "Backup systems failing to complete scheduled backups",
        "Monitoring systems showing false alerts",
        "Integration systems experiencing data synchronization issues",
        "User support experiencing high ticket volumes"
    ],
    "hr": [
        "Employee relations showing increased conflict reports",
        "Training programs not meeting completion targets",
        "Performance management processes showing delays",
        "Recruitment processes experiencing candidate quality issues",
        "Benefits administration showing processing errors",
        "Workplace safety showing increased incident reports",
        "Compliance training not meeting regulatory requirements",
        "Policy management showing outdated procedures",
        "Employee development programs showing low participation",
        "Compensation processes experiencing calculation errors",
        "Workplace culture showing declining satisfaction scores",
        "Diversity & inclusion initiatives showing limited progress"
    ],
    "sales": [
        "Customer relations showing declining satisfaction",
        "Sales processes experiencing efficiency issues",
        "Pricing strategy not meeting market competitiveness",
        "Market analysis showing outdated information",
        "Lead generation not meeting conversion targets",
        "Sales training showing low completion rates",
        "Customer support experiencing response delays",
        "Sales reporting showing data accuracy issues",
        "Territory management showing coverage gaps",
        "Product knowledge showing training gaps",
        "Negotiation processes showing poor outcomes",
        "Sales tools showing functionality issues"
    ]
}

SOLUTIONS = [
    "Implemented enhanced quality control procedures with additional inspection checkpoints",
    "Updated supplier specifications and conducted comprehensive supplier training",
    "Modified assembly procedures to include additional verification steps",
    "Enhanced testing protocols with more rigorous acceptance criteria",
    "Implemented root cause analysis and corrective action procedures",
    "Updated design specifications to address identified failure modes",
    "Enhanced material selection criteria based on performance testing results",
    "Implemented preventive maintenance schedules for critical equipment",
    "Updated training programs to address identified knowledge gaps",
    "Enhanced documentation and standard operating procedures",
    "Implemented continuous improvement processes with regular reviews",
    "Updated supplier contracts with enhanced quality requirements",
    "Enhanced communication protocols between departments",
    "Implemented advanced monitoring and alerting systems",
    "Updated risk assessment procedures with enhanced mitigation strategies"
]

MISSED_DETECTIONS = [
    "Visual inspection criteria were not specific enough to catch subtle defects",
    "Automated testing equipment was not calibrated to detect this type of issue",
    "Sampling frequency was insufficient to catch intermittent problems",
    "Testing procedures did not account for environmental conditions",
    "Quality control checkpoints were not positioned optimally in the process",
    "Inspection personnel were not adequately trained on this specific issue",
    "Testing equipment was not sensitive enough to detect the problem",
    "Process monitoring systems were not configured to alert on this condition",
    "Supplier quality audits did not cover this specific area",
    "Design validation testing did not include this failure mode",
    "Material testing protocols were not comprehensive enough",
    "Assembly verification procedures were not detailed enough"
]

def get_random_date_within_last_year() -> datetime:
    """Generate a random date within the last year"""
    now = datetime.utcnow()
    one_year_ago = now - timedelta(days=365)
    random_days = random.randint(0, 365)
    return one_year_ago + timedelta(days=random_days)

def get_severity_distribution() -> SeverityLevel:
    """Generate severity levels with realistic distribution"""
    weights = [0.4, 0.3, 0.2, 0.1]  # low, medium, high, critical
    return random.choices(
        [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL],
        weights=weights
    )[0]

def generate_realistic_incident(department: str) -> Dict[str, Any]:
    """Generate a realistic incident for a given department"""
    
    # Get department-specific data
    department_commodities = COMMODITIES.get(department, COMMODITIES["engineering"])
    department_problems = PROBLEM_SCENARIOS.get(department, PROBLEM_SCENARIOS["engineering"])
    
    # Generate incident data
    commodity = random.choice(department_commodities)
    part_number = random.choice(PART_NUMBERS)
    supplier = random.choice(SUPPLIERS)
    error_location = random.choice(ERROR_LOCATIONS)
    problem_description = random.choice(department_problems)
    missed_detection = random.choice(MISSED_DETECTIONS)
    provided_solution = random.choice(SOLUTIONS)
    reporter_name = random.choice(REPORTER_NAMES)
    severity = get_severity_distribution()
    created_at = get_random_date_within_last_year()
    
    return {
        "commodity": commodity,
        "part_number": part_number,
        "supplier": supplier,
        "error_location": error_location,
        "problem_description": problem_description,
        "missed_detection": missed_detection,
        "provided_solution": provided_solution,
        "department": department,
        "severity": severity,
        "reporter_name": reporter_name,
        "created_at": created_at
    }

async def generate_and_insert_data(num_incidents_per_department: int = 10):
    """Generate and insert synthetic incident data"""
    
    print(f"🚀 Starting synthetic data generation...")
    print(f"📊 Generating {num_incidents_per_department} incidents per department")
    print(f"🏢 Total departments: {len(DEPARTMENTS)}")
    print(f"📈 Total incidents to generate: {len(DEPARTMENTS) * num_incidents_per_department}")
    
    # Initialize database
    print("\n🔧 Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Generate and insert data
    total_inserted = 0
    
    async with AsyncSessionLocal() as session:
        for department in DEPARTMENTS:
            print(f"\n📝 Generating incidents for {department} department...")
            
            for i in range(num_incidents_per_department):
                incident_data = generate_realistic_incident(department)
                
                # Create LessonLearned object
                lesson = LessonLearned(**incident_data)
                session.add(lesson)
                
                if (i + 1) % 5 == 0:
                    print(f"   ✅ Generated {i + 1}/{num_incidents_per_department} incidents")
            
            # Commit batch for this department
            await session.commit()
            total_inserted += num_incidents_per_department
            print(f"   💾 Committed {num_incidents_per_department} incidents for {department}")
    
    print(f"\n🎉 Successfully generated and inserted {total_inserted} incidents!")
    print(f"📊 Data distribution:")
    
    # Show distribution by department
    async with AsyncSessionLocal() as session:
        for department in DEPARTMENTS:
            from sqlalchemy import select, func
            result = await session.execute(
                select(func.count(LessonLearned.id)).where(
                    LessonLearned.department == department
                )
            )
            count = result.scalar()
            print(f"   {department}: {count} incidents")
    
    print(f"\n✨ Synthetic data generation complete!")
    print(f"🌐 You can now test the system at: http://localhost:3000")

async def main():
    """Main function to run the synthetic data generator"""
    
    print("=" * 60)
    print("🏭 BMW Incident Reporting System - Synthetic Data Generator")
    print("=" * 60)
    
    try:
        # Get user input for number of incidents per department
        while True:
            try:
                num_incidents = input("\n📊 How many incidents per department? (default: 10): ").strip()
                if not num_incidents:
                    num_incidents = 10
                else:
                    num_incidents = int(num_incidents)
                
                if num_incidents < 1 or num_incidents > 100:
                    print("❌ Please enter a number between 1 and 100")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Confirm before proceeding
        total_incidents = len(DEPARTMENTS) * num_incidents
        confirm = input(f"\n⚠️  This will generate {total_incidents} total incidents. Continue? (y/N): ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled")
            return
        
        # Generate data
        await generate_and_insert_data(num_incidents)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error generating synthetic data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
