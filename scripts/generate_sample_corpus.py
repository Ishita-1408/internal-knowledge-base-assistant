"""
Generates the comprehensive synthetic sample document corpus for NovaTech demo & portfolio evaluation.
Creates 8 rich, internally consistent documents in PDF, DOCX, and TXT formats (approx 500-900 words each).
"""

import io
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
import pymupdf

SAMPLE_DIR = Path("sample_docs")
SAMPLE_DIR.mkdir(exist_ok=True)


def create_pdf(filename: str, title: str, sections: list):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    y = 45
    margin_x = 54
    line_h = 12.5
    
    # Title
    page.insert_text((margin_x, y), title, fontsize=15, fontname="helv", color=(0.1, 0.2, 0.5))
    y += 24
    
    for heading, paragraphs in sections:
        if y > 710:
            page = doc.new_page(width=612, height=792)
            y = 45
        
        # Heading
        page.insert_text((margin_x, y), heading, fontsize=11, fontname="helv", color=(0.15, 0.15, 0.15))
        y += 16
        
        for para in paragraphs:
            words = para.split(" ")
            current_line = []
            for w in words:
                current_line.append(w)
                if len(" ".join(current_line)) > 84:
                    page.insert_text((margin_x, y), " ".join(current_line[:-1]), fontsize=9, fontname="helv")
                    y += line_h
                    if y > 730:
                        page = doc.new_page(width=612, height=792)
                        y = 45
                    current_line = [w]
            if current_line:
                page.insert_text((margin_x, y), " ".join(current_line), fontsize=9, fontname="helv")
                y += line_h
            y += 5
            if y > 730:
                page = doc.new_page(width=612, height=792)
                y = 45
        y += 8
    
    doc.save(SAMPLE_DIR / filename)
    doc.close()
    print(f"Created PDF: {filename}")


def create_docx(filename: str, title: str, sections: list):
    doc = docx.Document()
    doc.add_heading(title, level=0)
    for heading, paragraphs in sections:
        doc.add_heading(heading, level=1)
        for para in paragraphs:
            doc.add_paragraph(para)
    doc.save(SAMPLE_DIR / filename)
    print(f"Created DOCX: {filename}")


def create_txt(filename: str, title: str, sections: list):
    lines = [f"{title.upper()}", "=" * len(title), ""]
    for heading, paragraphs in sections:
        lines.append(f"## {heading}")
        lines.append("")
        for para in paragraphs:
            lines.append(para)
            lines.append("")
    (SAMPLE_DIR / filename).write_text("\n".join(lines), encoding="utf-8")
    print(f"Created TXT: {filename}")


def main():
    # 1. Remote Work Policy (PDF)
    create_pdf(
        "Remote_Work_Policy.pdf",
        "NovaTech Remote Work and Distributed Team Policy (v3.2)",
        [
            ("1. Purpose and Operational Philosophy", [
                "NovaTech operates as a distributed-first technology company. This policy defines eligibility rules, financial stipends, hardware allocation, working hours, and security requirements for all full-time employees and contractors.",
                "Our philosophy prioritizes asynchronous communication, high documentation hygiene, and measurable output over physical presence."
            ]),
            ("2. Classification of Work Models and Eligibility", [
                "All NovaTech employees are assigned to one of three official work models upon offer acceptance:",
                "Remote-First: Employees whose primary residential address is situated more than 50 miles from any designated NovaTech regional hub (New York, San Francisco, London, Austin). Remote-first employees work from home full-time.",
                "Hybrid: Employees situated within 50 miles of a regional hub. Hybrid employees are required to work on-site at the hub 2 days per week on designated company collaboration days: Tuesdays and Thursdays. The remaining three days may be worked remotely.",
                "Dedicated In-Office: Roles requiring direct physical access to hardware laboratories, IT shipping depots, or facilities infrastructure.",
                "Full-time new hires become eligible for fully flexible remote scheduling immediately upon the successful completion of their mandatory 90-day probationary review."
            ]),
            ("3. Home Office Setup Stipend and Recurring Technology Allowance", [
                "To establish an ergonomic, productive home workspace, NovaTech provides every new full-time remote employee with a one-time Home Office Equipment Stipend of up to $1,000 USD.",
                "Eligible items for reimbursement under the setup stipend include motorized standing desks, ergonomic task chairs, external 4K monitors, monitor arms, ergonomic keyboards, mice, webcams, and noise-canceling headsets. Non-eligible items include decorative furniture, standing desk converters, audio speakers, and gaming peripherals.",
                "Stipend claims must be submitted with itemized vendor receipts via Expensify within the employee's first 60 calendar days of employment.",
                "In addition to the one-time setup stipend, all remote and hybrid employees receive a recurring Technology & Internet Allowance of $600 USD per year ($50 USD monthly), credited automatically on the final payroll cycle of each month to offset high-speed broadband costs."
            ]),
            ("4. Corporate Hardware Provisioning & Refresh Cadence", [
                "NovaTech IT procures, configures, and ships one primary corporate workstation to every employee prior to Day 1:",
                "Engineering, Product Design, and Data Science personnel receive a 16-inch Apple MacBook Pro configured with Apple Silicon M3 Max, 32GB Unified Memory, and 1TB SSD.",
                "Operations, Finance, Legal, and People Operations personnel receive a Lenovo ThinkPad X1 Carbon Gen 12 configured with Intel Core Ultra 7, 32GB RAM, and 512GB SSD.",
                "All workstations are enrolled in automated Mobile Device Management (MDM) with mandatory full-disk encryption (FileVault on macOS, BitLocker on Windows). Primary workstations are eligible for an automated hardware refresh every 36 months of active service."
            ]),
            ("5. Working Hours & Core Collaboration Window", [
                "To maintain predictable cross-functional communication across time zones, all distributed team members must maintain daily active availability on Slack during the Core Collaboration Window: 10:00 AM to 3:00 PM Eastern Standard Time (EST), Monday through Friday.",
                "Flexible scheduling outside the core window is permitted with direct manager notification, provided team commitments, standups, and customer-facing deliverables are fulfilled."
            ]),
            ("6. International Remote Work & Coworking Day Passes", [
                "Employees in good standing may temporarily work from an international location outside their legal country of residence for up to 30 consecutive business days per calendar year. Requests must be submitted to People Operations at least 15 business days in advance to evaluate corporate tax Nexus and GDPR/cross-border data privacy rules.",
                "For remote-first employees desiring occasional office space, NovaTech reimburses flexible on-demand coworking day passes (e.g. WeWork, Industrious) up to a maximum of $150 USD per calendar month with Director pre-approval."
            ])
        ]
    )

    # 2. Leave & Attendance Policy (DOCX)
    create_docx(
        "Leave_and_Attendance_Policy.docx",
        "NovaTech Employee Leave, Attendance, and Time-Off Policy (v4.0)",
        [
            ("1. Policy Overview and Work-Life Harmony", [
                "NovaTech recognizes that personal well-being, rest, and time away from work are essential for long-term creativity, health, and team success. This policy details the accrual, usage, approval mechanisms, and limits for all paid and unpaid leave categories."
            ]),
            ("2. Paid Time Off (PTO) Accrual Schedule & Rollover Caps", [
                "All regular full-time employees accrue Paid Time Off (PTO) on each semi-monthly pay period starting from their first day of active employment:",
                "Tenure Years 1 through 3: Employees accrue 20 business days (160 working hours) of PTO per calendar year, accruing at the rate of 1.66 days per completed calendar month.",
                "Tenure Year 4 and above: Beginning on the employee's fourth employment anniversary, annual PTO accrual increases to 25 business days (200 working hours) per calendar year, accruing at 2.08 days per completed month.",
                "Rollover Limits: Employees may roll over a maximum of 5 unused PTO days (40 hours) into the subsequent calendar year. All rolled-over PTO must be fully utilized on or before March 31 of the new year; any remaining rolled-over days after March 31 will expire without cash compensation.",
                "PTO Payout at Separation: Accrued but unused standard PTO will be paid out upon separation of employment in accordance with applicable state and local labor statutes."
            ]),
            ("3. Sick Leave, Medical Appointments & Wellness Days", [
                "NovaTech provides 10 dedicated paid sick days per calendar year, fully front-loaded on January 1 for all existing employees (prorated for mid-year new hires).",
                "Sick leave covers personal physical or mental illness, preventive medical visits, diagnostic appointments, and caring for an immediate family member requiring medical attention.",
                "Medical Documentation: If an employee is absent due to illness for more than 3 consecutive business days, a formal medical clearance note from a certified healthcare practitioner must be provided to People Operations upon return."
            ]),
            ("4. Comprehensive Parental Leave (Birth, Adoption & Foster)", [
                "NovaTech provides 16 consecutive weeks of 100% fully paid parental leave to eligible full-time employees following the birth of a child, adoption of a child, or placement of a foster child. This policy applies equally to all primary and secondary caregivers who have completed at least 6 months of continuous service.",
                "Parental leave must be concluded within the first 12 months of the qualifying event. Employees may take the 16 weeks as a single continuous block or split it into two equal 8-week blocks with manager and HR approval."
            ]),
            ("5. Bereavement, Jury Duty & Civic Leave", [
                "Bereavement Leave: Employees receive up to 5 consecutive paid business days in the event of the loss of an immediate family member (spouse, domestic partner, child, parent, or sibling), and up to 3 consecutive paid business days for extended family (grandparent, grandchild, aunt, uncle, in-law).",
                "Jury Duty & Court Subpoenas: NovaTech provides up to 10 paid business days of leave for mandatory jury duty or court appearances.",
                "Voting Leave: Employees whose work schedules do not allow for 3 consecutive non-working hours while polling locations are open receive up to 2 hours of paid time off to vote in local and national elections."
            ]),
            ("6. Public Holidays and Annual Company Winter Shutdown", [
                "NovaTech officially observes 11 standard federal public holidays annually (including New Year's Day, MLK Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving Day, and Christmas Day).",
                "In addition to public holidays, NovaTech observes an annual paid Winter Shutdown spanning from December 24 through January 1 inclusive. All normal product development and business operations are paused during this period, and it is not deducted from employee PTO balances."
            ]),
            ("7. Submission Procedures & Advance Notice Requirements", [
                "Planned time-off requests exceeding 3 consecutive business days must be formally submitted in Workday at least 10 business days in advance.",
                "Requests are routed to the employee's direct manager for approval based on project deadlines and operational team coverage."
            ])
        ]
    )

    # 3. Travel & Expense Policy (DOCX)
    create_docx(
        "Travel_and_Expense_Policy.docx",
        "NovaTech Corporate Travel & Expense Reimbursement Policy (v2.8)",
        [
            ("1. Purpose, Scope and Guiding Principles", [
                "This policy governs all business-related travel, lodging, meal expenses, client entertainment, and professional incidentals incurred by NovaTech employees. Employees are expected to exercise good judgment and spend corporate funds judiciously as fiduciary stewards."
            ]),
            ("2. Corporate Travel Booking Portal & Airfare Standards", [
                "All commercial flights must be booked exclusively through NovaTech's corporate travel management tool (Navan) using the company credit card on file.",
                "Domestic Airfare: Economy class booking is mandatory for all domestic flights within North America.",
                "International Airfare: Economy class is required for international flights under 6 continuous flight hours. Premium Economy or Business Class travel is permitted for international flights exceeding 8 continuous flight hours, subject to written pre-authorization from the functional Vice President.",
                "Seat upgrades, priority boarding fees, and airline lounge memberships are considered personal expenses and are strictly non-reimbursable."
            ]),
            ("3. Hotel Lodging Nightly Maximum Rates", [
                "Hotel rooms must be booked in standard single-occupancy rooms through Navan. Nightly room rate maximums (excluding local taxes and mandatory resort fees) are tiered by destination city:",
                "Tier 1 Metropolitan Markets (New York City, San Francisco, London, Tokyo, Zurich, Singapore, Paris): Maximum rate of $300 USD per night.",
                "Tier 2 Markets (all other domestic and international urban locations): Maximum rate of $200 USD per night.",
                "If hotels within the designated cap are unavailable due to city-wide conventions or peak seasonal events, written pre-approval from a Department Director is required prior to booking."
            ]),
            ("4. Daily Meal Reimbursement and Client Entertainment", [
                "Individual Travel Meals: When traveling on authorized business, NovaTech reimburses actual meal costs up to a maximum daily per diem of $85 USD per day. Recommended allocation: $20 for breakfast, $25 for lunch, and $40 for dinner. Itemized receipts are mandatory for any single meal expense exceeding $25 USD.",
                "Alcohol Policy: Alcoholic beverages purchased during solo travel meals are strictly non-reimbursable.",
                "Team Dinners & Client Entertainment: Authorized client entertainment dinners or internal team celebratory meals are capped at $100 USD per attendee (including food, beverage, tax, and gratuity). An itemized receipt accompanied by a complete list of attendee names, affiliations, and business discussion topics must be attached in Expensify."
            ]),
            ("5. Ground Transportation, Rental Cars & Airport Parking", [
                "Rideshare & Taxis: Standard rideshare options (UberX, Lyft Standard) or municipal licensed taxis are fully reimbursable for travel between airports, lodging, and client offices. Premium luxury vehicles (Uber Black, Lyft Lux) are strictly prohibited.",
                "Rental Cars: Compact or intermediate sedans should be booked via Navan. Rental car optional collision damage waivers (CDW) should be declined domestically as NovaTech corporate insurance covers rental vehicles.",
                "Personal Mileage: Business use of personal vehicles is reimbursed at the prevailing IRS federal mileage rate (currently $0.67 per mile). Commuting from home to the local hub office is non-reimbursable.",
                "Airport Parking: Long-term economy airport parking is reimbursed up to a maximum of $35 USD per calendar day."
            ]),
            ("6. Expense Filing Windows and Management Approval Matrix", [
                "Expense reports must be submitted in Expensify within 30 calendar days of incurring the expense or completing the travel event. Expense submissions older than 60 calendar days will be automatically rejected without reimbursement.",
                "Management Approval Thresholds:",
                "Level 1: Direct Managers can approve individual expense reports up to $2,500 USD.",
                "Level 2: Department Directors must approve expense reports between $2,501 and $10,000 USD.",
                "Level 3: The Chief Financial Officer (CFO) must approve any expense report exceeding $10,000 USD."
            ])
        ]
    )

    # 4. Employee Onboarding Guide (PDF)
    create_pdf(
        "Employee_Onboarding_Guide.pdf",
        "NovaTech New Hire Onboarding Guide & First 90 Days Roadmap",
        [
            ("1. Welcome to the NovaTech Team", [
                "Welcome to NovaTech! This onboarding guide is your operational roadmap for navigating administrative tasks, technical provisioning, compliance requirements, and performance milestones during your first 90 days with the company."
            ]),
            ("2. Day 1 Logistics, Orientation & Account Provisioning", [
                "Welcome Session: Your first day starts at 9:30 AM EST with a live virtual Welcome & Orientation session hosted by the People Operations team on Zoom.",
                "Account Activation: Check your personal email for the Okta Single Sign-On (SSO) invitation link to set up your primary credentials and activate corporate email and Google Workspace access.",
                "Multi-Factor Authentication (MFA): Register your hardware YubiKey or Google Authenticator app for two-factor authentication. SMS-based 2FA is prohibited under the Information Security Policy.",
                "Slack Channels: Join standard team channels on Slack including #general, #announcements, #team-celebrations, #kba-internal-help, and your specific functional squad channel."
            ]),
            ("3. First Week Milestones (Days 1–5 Checklist)", [
                "Complete Compliance Training: Access the NovaTech Learning Portal and complete three mandatory training courses within your first 5 business days: (1) Information Security & Data Protection Awareness, (2) Workplace Diversity & Anti-Harassment, and (3) Corporate Code of Business Conduct.",
                "Benefits Enrollment: Review health, dental, vision, life insurance, and 401(k) retirement matching plans in BambooHR. You have a 30-calendar-day enrollment window from your official hire date to finalize benefit selections.",
                "Submit Home Office Stipend: Purchase eligible home office equipment (desk, chair, monitor) and submit receipts in Expensify for the $1,000 one-time Home Office Equipment Stipend per the Remote Work Policy.",
                "Onboarding Buddy Pairing: You will be paired with a seasoned Onboarding Buddy for your first 60 days. Schedule an introductory virtual coffee chat during your first week to learn team workflows, informal norms, and internal tooling tips."
            ]),
            ("4. First Month Milestones (Days 6–30)", [
                "Set Up Weekly 1-on-1s: Establish a recurring weekly 1-on-1 meeting cadence with your direct manager. Review team quarterly OKRs, sprint backlogs, and active product roadmaps.",
                "Development Environment Setup: Engineering new hires should clone core GitHub repositories, configure local development containers using Docker, and request necessary AWS IAM roles or database read credentials via Jira Service Desk.",
                "Day 30 Check-in: Conduct a formal 30-day alignment meeting with your manager to evaluate initial onboarding progress, review completed ramp-up tasks, and set 60-day project goals."
            ]),
            ("5. 60 and 90-Day Milestones & Probation Completion", [
                "Day 60 Milestone: Ship your first independent project, production feature, or technical document. Participate actively in sprint planning and team retrospectives.",
                "Day 90 Probationary Review: Complete your formal 90-Day Probationary Review with your manager and People Operations HR Business Partner. Successful completion transitions you from probationary status to regular full-time employee standing, unlocking international remote work eligibility."
            ])
        ]
    )

    # 5. Q1 Product Roadmap (DOCX)
    create_docx(
        "Q1_Product_Roadmap.docx",
        "NovaTech Q1 2026 Product Strategy & Engineering Roadmap",
        [
            ("1. Strategic Overview and Executive Vision", [
                "During Q1 2026 (January 1 – March 31, 2026), NovaTech Engineering and Product teams are focused on laying the core foundation for the Internal Knowledge-Base Assistant (KBA). Our core objectives center on multi-source ingestion, vector storage stability, query-time permission enforcement, and multi-platform client accessibility."
            ]),
            ("2. Key Q1 Strategic Themes and Planned Feature Deliverables", [
                "Theme 1 — Google Drive Connector V1: Develop production connector integrating with Google Drive API v3. Must support OAuth2 authorization, automated plain-text extraction for Google Docs, Sheets, and Slides, PyMuPDF extraction for PDFs, and python-docx parsing for Word files. Must incorporate Drive Changes API for incremental sync polling. Target Completion Date: February 28, 2026. Status: On Track.",
                "Theme 2 — Permission-Aware Vector Retrieval Filter: Build a query-time security filter in retrieval/permission_filter.py ensuring that retrieved ChromaDB chunks are filtered against user ACL email addresses before passing into the LLM generation prompt (see ADR 001). Target Completion Date: March 15, 2026. Status: Complete.",
                "Theme 3 — Vector Store Optimization: Migrate from ephemeral in-memory embeddings to ChromaDB persistent storage using HNSW cosine distance indexing to maintain sub-second retrieval latency on collections up to 100,000 chunks. Target Completion Date: March 20, 2026. Status: On Track.",
                "Theme 4 — Mobile Knowledge Assistant MVP: Develop cross-platform mobile search client on iOS and Android using React Native, enabling traveling employees to query company documents from mobile devices. Target Completion Date: March 31, 2026. Status: At Risk due to mobile engineering resource constraints and competing backend API priorities."
            ]),
            ("3. Engineering Resource Allocations", [
                "Core Ingestion & RAG Retrieval Pipeline: 8 Backend Engineers, 1 Machine Learning Engineer.",
                "Streamlit Web UI & Metrics Dashboard: 4 Frontend Engineers, 1 Product Designer.",
                "Mobile Knowledge Assistant: 3 Mobile Engineers."
            ]),
            ("4. Identified Risks & Technical Dependencies", [
                "The Drive Connector rollout depends upon Google Cloud Workspace OAuth app security verification.",
                "ChromaDB persistent client performance requires careful calibration of distance thresholds to prevent false no-answer fallback triggers on paraphrase queries (see ADR 004)."
            ])
        ]
    )

    # 6. Q2 Product Roadmap (PDF)
    create_pdf(
        "Q2_Product_Roadmap.pdf",
        "NovaTech Q2 2026 Product Strategy & Engineering Roadmap",
        [
            ("1. Executive Summary & Review of Q1 Outcomes", [
                "This document establishes NovaTech's strategic engineering priorities for Q2 2026 (April 1 – June 30, 2026). During Q1 2026, the team successfully shipped the Google Drive Connector V1 and completed the Permission-Aware Retrieval Filter ahead of schedule.",
                "Strategic Shift & Deprioritization: Following an executive review of Q1 outcomes, the Mobile Knowledge Assistant MVP was officially deprioritized and postponed from Q1 to Q4 2026. Engineering resources were reallocated entirely to RAG answer accuracy, a rigorous 3-layer evaluation framework, in-memory stream extraction, and real-time cost attribution."
            ]),
            ("2. Core Q2 Strategic Priorities and Target Deliverables", [
                "Priority 1 — 3-Layer Evaluation Benchmark Suite: Build an enterprise-grade evaluation pipeline measuring Retrieval Metrics (Recall@K, Precision@K, MRR), LLM Scorer Metrics (Groundedness, Answer Correctness, Citation Accuracy, Hallucination Rate), and Product Metrics (Query Resolution Rate, Response Latency, Feedback Satisfaction). Ships with automated markdown reporting in docs/eval-report.md. Target Completion Date: April 30, 2026.",
                "Priority 2 — Token Usage & Cost Attribution Engine: Implement real-time token tracking per query with model-level USD cost estimation across Gemini, OpenAI, and open-source models to ensure complete financial visibility. Target Completion Date: May 15, 2026.",
                "Priority 3 — High-Performance In-Memory Ingestion Pipeline: Build pure in-memory DOCX and PDF byte stream extraction via PyMuPDF and python-docx BytesIO, eliminating disk I/O bottlenecks and temporary file overhead during Drive and local synchronization. Target Completion Date: May 30, 2026.",
                "Priority 4 — Phase 2 Connector Scoping: Define abstract connector interfaces for future Notion and Confluence integrations, preserving modular connector boundaries without implementing production connectors in V1. Target Completion Date: June 30, 2026."
            ]),
            ("3. Engineering Team Reallocation", [
                "Evaluation & Quality Engineering: 5 Engineers dedicated to benchmark datasets, scorer rubrics, and automated regression suites.",
                "Core RAG Pipeline & Ingestion: 7 Engineers dedicated to in-memory extraction, ChromaDB persistence, and token tracking.",
                "Web Application & Analytics Dashboard: 3 Engineers dedicated to Streamlit metrics dashboard."
            ])
        ]
    )

    # 7. Information Security Policy (TXT)
    create_txt(
        "Information_Security_Policy.txt",
        "NovaTech Information Security Policy and Data Protection Standards (v5.1)",
        [
            ("1. Policy Classification and Access Authorization", [
                "CLASSIFICATION: RESTRICTED.",
                "ACCESS CONTROL LIST (ACL): Restricted exclusively to authorized security personnel and system administrators: security-team@example.com, admin@example.com.",
                "This document outlines mandatory information security controls, encryption mandates, credential rotation protocols, and incident response SLAs across NovaTech infrastructure."
            ]),
            ("2. Authentication, MFA Mandate & Password Standards", [
                "Multi-Factor Authentication (MFA): Strong MFA is mandatory for all employee and contractor accounts accessing NovaTech systems. Approved authentication methods include FIDO2/WebAuthn hardware security keys (YubiKey) or time-based one-time password (TOTP) applications (1Password, Google Authenticator). SMS-based 2FA is explicitly prohibited across all systems.",
                "Password Complexity: User account passwords must be at least 16 characters in length and include uppercase letters, lowercase letters, numbers, and symbols. Passwords must be generated and stored in corporate 1Password vaults.",
                "SSH Keys & API Token Rotation: Production SSH keys, database credentials, and cloud API tokens must be rotated every 90 days. Unused service account credentials older than 30 days are automatically disabled."
            ]),
            ("3. Data Classification and Encryption Standards", [
                "NovaTech data is categorized into four strict classification tiers:",
                "Public: Marketing brochures, open-source repositories, and public documentation.",
                "Internal: General employee policies, standard onboarding guides, and company-wide announcements.",
                "Confidential: Product strategy roadmaps, financial models, vendor contracts, and unreleased feature specifications.",
                "Restricted: Production database records, customer PII, encryption keys, security audit logs, and employee compensation data.",
                "Encryption Mandates: All data at rest must be encrypted using AES-256 encryption across storage disks, AWS S3 buckets, and ChromaDB vector collections. All data in transit must strictly enforce TLS 1.3 encryption."
            ]),
            ("4. Security Incident Response Protocol and SLAs", [
                "Security incidents are categorized into three severity tiers, each with strict response SLAs:",
                "Severity 0 (Critical — Active data breach, root credential compromise, or active exfiltration): Maximum 15-minute response SLA. An Incident Commander must be designated within 30 minutes; executive leadership and legal counsel must be briefed within 2 hours.",
                "Severity 1 (High — Critical zero-day vulnerability in production or single-point failure affecting authentication): Maximum 1-hour response SLA. Mitigation plan required within 4 hours.",
                "Severity 2 (Medium — Policy non-compliance or minor security alerts without data exposure): Maximum 8-hour response SLA."
            ]),
            ("5. Clean Desk, Screen Lock and Device Security Policy", [
                "Screen Lock: All workstations must automatically lock screens after 5 minutes of inactivity.",
                "Full-Disk Encryption: FileVault (macOS) or BitLocker (Windows) full-disk encryption is mandatory and enforced via Kandji MDM.",
                "Removable Media: Employees are strictly prohibited from copying corporate data to personal USB flash drives or unapproved third-party cloud storage."
            ])
        ]
    )

    # 8. Performance Review Guidelines (DOCX)
    create_docx(
        "Performance_Review_Guidelines.docx",
        "NovaTech Performance Review, Calibration, and Compensation Guidelines (v2.0)",
        [
            ("1. Policy Classification and Confidentiality", [
                "CONFIDENTIAL — RESTRICTED TO PEOPLE MANAGERS AND HR PERSONNEL.",
                "ACCESS CONTROL LIST (ACL): Restricted to hr@example.com, manager@example.com.",
                "This document provides guidelines for performance evaluations, 5-tier calibration curves, promotion criteria, and merit salary adjustment bands."
            ]),
            ("2. Performance Review Cadence & Evaluation Cycles", [
                "NovaTech conducts formal performance reviews twice per calendar year:",
                "Mid-Year Review Cycle (June 1 – June 30): Focuses on progress against annual OKRs, qualitative 360-degree feedback, and coaching conversations. Does not impact base salary.",
                "Annual Review Cycle (November 1 – December 15): Comprehensive evaluation determining merit salary increases, annual performance bonus payouts, equity refreshes, and level promotions.",
                "Evaluation Steps: (1) Employee self-assessment submitted within the first 10 days of the cycle, (2) Minimum of 3 peer reviews gathered via Lattice, (3) Manager assessment and rating submission, (4) Departmental calibration committee review."
            ]),
            ("3. 5-Tier Rating Scale and Calibration Curve", [
                "To maintain fairness and consistency across teams, manager ratings are calibrated against the following distribution targets:",
                "Rating 1 — Does Not Meet Expectations (Target: <5% of organization): Performance consistently fails to meet role requirements. Triggers an immediate 60-day Performance Improvement Plan (PIP). Ineligible for bonus, promotion, or merit increase.",
                "Rating 2 — Inconsistently Meets Expectations (Target: ~15% of organization): Meets some objectives but lacks consistency in delivery or cross-functional collaboration. Eligible for partial bonus (0.5x target).",
                "Rating 3 — Consistently Meets Expectations (Target: ~55% of organization): Solid core contributor who consistently meets all expectations and core values. Eligible for 1.0x target bonus.",
                "Rating 4 — Exceeds Expectations (Target: ~20% of organization): Consistently delivers high-impact outcomes exceeding role scope. Eligible for 1.25x target bonus multiplier.",
                "Rating 5 — Outstanding Impact (Target: ~5% of organization): Exceptional organizational impact and technical or business leadership. Eligible for 1.5x target bonus multiplier and priority promotion review."
            ]),
            ("4. Promotion Eligibility Criteria", [
                "Formal level promotions occur exclusively during the Q4 Annual Review Cycle.",
                "Eligibility Requirements: Employee must have a minimum tenure of 12 consecutive months at their current level and have achieved a performance rating of 4 or 5 in the preceding review cycle.",
                "Promotion Dossier: Requires written sponsorship from the direct manager, two cross-functional staff-level peer recommendations, and sign-off from the Department Vice President and People Review Board."
            ]),
            ("5. Annual Merit Salary Increase Bands", [
                "Merit salary increases are tied directly to calibrated performance ratings:",
                "Rating 3 (Meets Expectations): 2.0% to 4.0% base salary increase.",
                "Rating 4 (Exceeds Expectations): 5.0% to 8.0% base salary increase.",
                "Rating 5 (Outstanding Impact): 9.0% to 14.0% base salary increase."
            ])
        ]
    )


if __name__ == "__main__":
    main()
