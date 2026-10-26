"""
Demo Data Generator for TenderCheck.
Generates realistic, high-quality PDFs for:
  1. GeM IT Hardware Tender (Laptops for Government Department)
  2. Vendor A: Meets every requirement
  3. Vendor B: Turnover too low, no OEM authorization, conflicting employee count
"""
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos


class GeMPDFBase(FPDF):
    def __init__(self, header_title: str, sub_title: str, doc_code: str):
        super().__init__()
        self.header_title = header_title
        self.sub_title = sub_title
        self.doc_code = doc_code

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(24, 43, 73)
        self.cell(0, 7, self.header_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, self.sub_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_draw_color(200, 200, 200)
        self.line(10, 22, 200, 22)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Doc Ref: {self.doc_code}", align="C")


def create_tender_pdf(output_path: Path):
    pdf = GeMPDFBase(
        header_title="GOVERNMENT E-MARKETPLACE (GeM) - BID DOCUMENT",
        sub_title="Directorate of Information Technology | Ministry of Electronics & IT | Bid Ref: GEM/2026/B/8821941",
        doc_code="GEM/2026/B/8821941",
    )
    pdf.alias_nb_pages()

    # --- Page 1: Invitation for Bids, Financial & Experience Criteria ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 8, "SECTION I: INVITATION FOR BIDS & ELIGIBILITY CRITERIA", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # Box: Scope
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(210, 220, 235)
    pdf.rect(10, 34, 190, 24, "DF")
    pdf.set_xy(12, 36)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 5, "1. Scope of Work:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        185, 4.5,
        "Supply, installation, testing, and 3-year on-site comprehensive warranty support of 120 units "
        "of Enterprise Grade Laptops for government administrative and field offices under Directorate of IT."
    )

    pdf.set_y(62)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 6, "2. Financial Criteria:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(
        0, 5,
        "2.1 Minimum Average Annual Turnover: The average annual turnover of the bidder during the last "
        "three financial years (FY 2022-23, FY 2023-24, and FY 2024-25) must be at least INR 2.00 Crore "
        "(Indian Rupees Two Crore only). The bidder must submit a CA certificate with unique document "
        "identification number (UDIN) and audited financial balance sheets."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 6, "3. Experience & Past Performance:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(
        0, 5,
        "3.1 Years in Business: The bidder must have at least 3 years of experience in the supply and maintenance "
        "of IT hardware, laptops, and computer systems to Central or State Government departments, PSUs, or Autonomous Bodies.\n"
        "3.2 Past Similar Orders: The bidder must have completed at least 2 similar orders for the supply of laptops "
        "or computing hardware in the preceding 3 years, with each completed order value not less than INR 50 Lakhs. "
        "Satisfactory completion certificates or client purchase orders must be enclosed."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 6, "4. Bid Validity & Delivery Terms:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(
        0, 5,
        "The quoted rates and bid shall remain valid for a minimum of 90 days from the bid submission closing date. "
        "Delivery, installation, and end-to-end commissioning must be completed within 30 days of award of contract."
    )

    # --- Page 2: Technical Specifications ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 8, "SECTION II: TECHNICAL SPECIFICATIONS FOR LAPTOPS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    specs = [
        ("Processor", "Intel Core i7 13th Generation or equivalent 10-core/12-core processor (min 2.4 GHz base frequency)."),
        ("RAM / Memory", "Minimum 16 GB DDR4/DDR5 high-speed RAM, expandable to at least 32 GB."),
        ("Storage (SSD)", "Minimum 512 GB M.2 NVMe PCIe Gen 4 high performance solid state drive (SSD)."),
        ("Display Size", "Minimum 14.0 inch Full HD (1920 x 1080) Anti-Glare IPS display with minimum 250 nits brightness."),
        ("Operating System", "Pre-installed genuine Windows 11 Professional 64-bit with OEM recovery partition and license."),
        ("Battery & Power", "Minimum 50 Wh lithium-ion battery supporting fast charging capability (up to 80% within 60 mins)."),
        ("Warranty", "Comprehensive on-site OEM warranty for minimum 3 years including parts, battery, and power adapter with 48-hour resolution.")
    ]

    for title, desc in specs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(42, 6, title + ":", border=0)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(1)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 6, "5. Warranty & Service Level Agreement (SLA):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(
        0, 5,
        "The bidder and OEM must guarantee comprehensive on-site warranty for a minimum period of 3 years "
        "from the date of successful commissioning. Any hardware or firmware defect must be resolved within 48 hours."
    )

    # --- Page 3: Mandatory Certifications & Compliance ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(0, 8, "SECTION III: MANDATORY CERTIFICATIONS & COMPLIANCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    certs = [
        ("ISO Certification", "The OEM and the Bidder must possess a valid ISO 9001:2015 quality management system certificate."),
        ("GST Registration", "The bidder must submit a valid GST Registration Certificate with active tax filing status."),
        ("BIS Registration", "The quoted laptop model must have valid BIS Registration under the CRS scheme of MEITY conforming to IS 13252."),
        ("OEM Authorization", "Bidders who are not OEMs must submit an authentic OEM Authorization Letter (MAF) issued specifically for Bid GEM/2026/B/8821941, committing 3-year direct warranty and spares support."),
        ("Make in India (MII)", "Purchase preference under PPP-MII policy will apply to Class I (local content >= 50%) and Class II (local content >= 20%) local suppliers."),
        ("Statutory Declaration", "Bidders must submit an authorized organizational declaration disclosing registered office, workforce strength, and financial standing.")
    ]

    for item, text in certs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 5, item + ":", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, text)
        pdf.ln(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    print(f"Generated Tender PDF: {output_path}")


def create_vendor_a_documents(folder: Path):
    """
    Vendor A: Apex Tech Solutions Pvt Ltd
    Meets every requirement:
      - Turnover: INR 3.40 Crore (> 2.00 Crore)
      - Experience: 5 years in business (> 3 years)
      - Past orders: 3 completed orders (> 50 Lakhs each)
      - Specs: i7 13th Gen, 16 GB DDR5 RAM, 512 GB SSD, 14.0 inch FHD IPS, 3 years warranty
      - Certificates: ISO 9001:2015, GST Active, BIS registered, OEM Authorization Letter (MAF)
      - Employee count: 65 full-time employees in both documents (consistent, no contradiction)
    """
    folder.mkdir(parents=True, exist_ok=True)

    # Document 1: Profile & Financials
    pdf1 = GeMPDFBase(
        header_title="APEX TECH SOLUTIONS PVT LTD - CORPORATE PROFILE & FINANCIALS",
        sub_title="Tender Submission: GEM/2026/B/8821941 | Directorate of Information Technology",
        doc_code="ATS/GEM/2026/DOC-01",
    )
    pdf1.alias_nb_pages()
    pdf1.add_page()
    pdf1.set_font("Helvetica", "B", 12)
    pdf1.set_text_color(20, 50, 100)
    pdf1.cell(0, 8, "COMPANY PROFILE & EXECUTIVE SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf1.set_font("Helvetica", "", 9)
    pdf1.set_text_color(40, 40, 40)
    pdf1.multi_cell(
        0, 5,
        "Apex Tech Solutions Pvt Ltd was incorporated in February 2019 and possesses over 5 years of experience "
        "in the supply, deployment, and lifecycle maintenance of enterprise IT hardware and computing solutions to "
        "Central Ministries, State Government departments, and Public Sector Undertakings (PSUs).\n\n"
        "Organizational Workforce: Apex Tech Solutions maintains a dedicated team of 65 full-time employees "
        "comprising certified hardware engineers, system architects, and technical support specialists across our "
        "headquarters and regional service centers."
    )
    pdf1.ln(4)

    pdf1.set_font("Helvetica", "B", 11)
    pdf1.set_text_color(20, 50, 100)
    pdf1.cell(0, 7, "FINANCIAL CRITERIA & AUDITED TURNOVER", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf1.set_font("Helvetica", "", 9)
    pdf1.set_text_color(40, 40, 40)
    pdf1.multi_cell(
        0, 5,
        "As certified by our Statutory Chartered Accountant (M/s R.K. Singhal & Associates, UDIN: 24098234AAAA9812), "
        "the annual turnover of Apex Tech Solutions Pvt Ltd during the preceding three financial years is as follows:\n"
        "  - Financial Year 2022-23: INR 2.90 Crore\n"
        "  - Financial Year 2023-24: INR 3.50 Crore\n"
        "  - Financial Year 2024-25: INR 3.80 Crore\n\n"
        "Average annual turnover of the bidder during the last three financial years is INR 3.40 Crore "
        "(Indian Rupees Three Crore Forty Lakhs only), which fully satisfies the tender turnover requirement of minimum INR 2.00 Crore."
    )
    pdf1.ln(4)

    pdf1.set_font("Helvetica", "B", 11)
    pdf1.set_text_color(20, 50, 100)
    pdf1.cell(0, 7, "PAST SIMILAR ORDERS & PERFORMANCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf1.set_font("Helvetica", "", 9)
    pdf1.set_text_color(40, 40, 40)
    pdf1.multi_cell(
        0, 5,
        "The bidder has successfully executed the following similar laptop supply contracts in the last 3 years:\n"
        "  1. Order Ref MRD/2023/IT-77: Supply of 140 Enterprise Laptops to Ministry of Rural Development, Order Value: INR 78 Lakhs (Completed November 2023).\n"
        "  2. Order Ref SPDC/2024/091: Supply of 110 Commercial Laptops to State Power Distribution Corp, Order Value: INR 62 Lakhs (Completed August 2024).\n"
        "  3. Order Ref NHM/2025/HW-14: Supply of 95 Laptops to National Health Mission, Order Value: INR 54 Lakhs (Completed February 2025).\n"
        "Total completed orders: 3 similar orders with each order value exceeding INR 50 Lakhs."
    )
    doc1_path = folder / "vendor_a_profile_and_financials.pdf"
    pdf1.output(str(doc1_path))
    print(f"Generated Vendor A Doc 1: {doc1_path}")

    # Document 2: Technical Bid & Specs
    pdf2 = GeMPDFBase(
        header_title="APEX TECH SOLUTIONS PVT LTD - TECHNICAL SPECIFICATIONS BID",
        sub_title="Tender Submission: GEM/2026/B/8821941 | Model: OptiBook Enterprise 14-G7",
        doc_code="ATS/GEM/2026/DOC-02",
    )
    pdf2.alias_nb_pages()
    pdf2.add_page()
    pdf2.set_font("Helvetica", "B", 12)
    pdf2.set_text_color(20, 50, 100)
    pdf2.cell(0, 8, "TECHNICAL SPECIFICATION COMPLIANCE SHEET", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf2.set_font("Helvetica", "", 9)
    pdf2.set_text_color(40, 40, 40)
    pdf2.multi_cell(
        0, 5,
        "We hereby quote our flagship Commercial Laptop Model 'OptiBook Enterprise 14-G7' manufactured by "
        "OptiTech Systems Global Inc. The detailed technical specifications are detailed below:"
    )
    pdf2.ln(3)

    specs_a = [
        ("Laptop Model", "OptiBook Enterprise 14-G7 Commercial Laptop"),
        ("Processor", "Intel Core i7 13th Generation (i7-13700H, 14 cores, 20 threads, 2.4 GHz base frequency up to 5.0 GHz turbo)."),
        ("RAM / Memory", "16 GB DDR5 4800MHz high-speed RAM (expandable up to 64 GB via 2 SODIMM slots)."),
        ("Storage (SSD)", "512 GB M.2 NVMe PCIe Gen 4 high performance solid state drive (SSD)."),
        ("Display Size", "14.0 inch Full HD (1920 x 1080) Anti-Glare IPS display with 300 nits brightness."),
        ("Operating System", "Pre-installed genuine Windows 11 Professional 64-bit with recovery partition and digital license."),
        ("Battery", "54 Wh lithium-ion battery supporting fast charging (up to 80% charge in 55 minutes)."),
        ("Warranty", "Comprehensive on-site OEM warranty for 3 years including parts, battery, adapter, and 24x7 helpdesk support with 48-hour resolution."),
    ]
    for label, val in specs_a:
        pdf2.set_font("Helvetica", "B", 9)
        pdf2.set_text_color(30, 30, 30)
        pdf2.cell(42, 6, label + ":", border=0)
        pdf2.set_font("Helvetica", "", 9)
        pdf2.set_text_color(50, 50, 50)
        pdf2.multi_cell(0, 6, val)
        pdf2.ln(1)

    pdf2.ln(4)
    pdf2.set_font("Helvetica", "B", 10)
    pdf2.set_text_color(20, 50, 100)
    pdf2.cell(0, 6, "BID VALIDITY STATEMENT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf2.set_font("Helvetica", "", 9)
    pdf2.set_text_color(40, 40, 40)
    pdf2.multi_cell(
        0, 5,
        "The quoted rates and bid shall remain valid for a period of 90 days from the bid submission closing date."
    )
    doc2_path = folder / "vendor_a_technical_bid_and_specs.pdf"
    pdf2.output(str(doc2_path))
    print(f"Generated Vendor A Doc 2: {doc2_path}")

    # Document 3: Compliance & Certifications
    pdf3 = GeMPDFBase(
        header_title="APEX TECH SOLUTIONS PVT LTD - COMPLIANCE & CERTIFICATES",
        sub_title="Tender Submission: GEM/2026/B/8821941 | Statutory Compliance Enclosures",
        doc_code="ATS/GEM/2026/DOC-03",
    )
    pdf3.alias_nb_pages()
    pdf3.add_page()
    pdf3.set_font("Helvetica", "B", 12)
    pdf3.set_text_color(20, 50, 100)
    pdf3.cell(0, 8, "MANDATORY STATUTORY & REGULATORY CERTIFICATES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf3.ln(2)

    certs_a = [
        ("ISO Certification", "Apex Tech Solutions Pvt Ltd and OEM OptiTech Systems possess a valid ISO 9001:2015 Quality Management System Certificate (Certificate No. QMS-IND-2023-9941, valid until 15-November-2027)."),
        ("GST Registration", "Valid GST Registration Certificate enclosed (GSTIN: 07AAACA1234F1Z8), Registration Status: Active and Regular taxpayer."),
        ("BIS Registration", "The quoted laptop model OptiBook Enterprise 14-G7 has valid BIS Registration under the CRS scheme of MEITY (Registration No. R-41089234 conforming to IS 13252 (Part 1):2010)."),
        ("OEM Authorization (MAF)", "Manufacturer's Authorization Form (MAF) from OEM OptiTech Systems Global Inc. specifically issued for GeM Bid Ref: GEM/2026/B/8821941, authorizing Apex Tech Solutions Pvt Ltd to quote and supply, and confirming 3 years comprehensive direct OEM warranty."),
        ("Make in India (MII)", "Make in India Certificate: OptiBook Enterprise 14-G7 has 58% local content and qualifies as a Class I Local Supplier under the PPP-MII policy."),
        ("Human Resources & ESI", "Statutory HR and ESI declaration: Apex Tech Solutions employs 65 full-time employees across technical support and corporate administration.")
    ]
    for label, val in certs_a:
        pdf3.set_font("Helvetica", "B", 9)
        pdf3.set_text_color(30, 30, 30)
        pdf3.cell(0, 5, label + ":", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf3.set_font("Helvetica", "", 9)
        pdf3.set_text_color(50, 50, 50)
        pdf3.multi_cell(0, 5, val)
        pdf3.ln(2)

    doc3_path = folder / "vendor_a_compliance_and_certifications.pdf"
    pdf3.output(str(doc3_path))
    print(f"Generated Vendor A Doc 3: {doc3_path}")


def create_vendor_b_documents(folder: Path):
    """
    Vendor B: Nexura Hardware Systems Ltd
    Issues:
      1. Turnover too low: Average annual turnover INR 0.85 Crore (required: INR 2.00 Crore) -> FAIL
      2. No OEM Authorization: Reseller, OEM MAF letter missing/not submitted -> MISSING
      3. Contradictory employee count between documents:
         - Document 1 (Company Profile): "120 full-time employees"
         - Document 2 (Financials & Compliance): "28 full-time employees"
         -> CONTRADICTION detected!
    """
    folder.mkdir(parents=True, exist_ok=True)

    # Document 1: Company Profile
    pdf1 = GeMPDFBase(
        header_title="NEXURA HARDWARE SYSTEMS LTD - COMPANY PROFILE & OVERVIEW",
        sub_title="Tender Submission: GEM/2026/B/8821941 | Directorate of Information Technology",
        doc_code="NHS/GEM/2026/DOC-01",
    )
    pdf1.alias_nb_pages()
    pdf1.add_page()
    pdf1.set_font("Helvetica", "B", 12)
    pdf1.set_text_color(120, 30, 30)
    pdf1.cell(0, 8, "COMPANY PROFILE & INFRASTRUCTURE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf1.set_font("Helvetica", "", 9)
    pdf1.set_text_color(40, 40, 40)
    pdf1.multi_cell(
        0, 5,
        "Nexura Hardware Systems Ltd was incorporated in August 2020 and has over 4 years of experience "
        "in delivering commercial IT hardware, desktops, and peripherals to regional government and commercial clients.\n\n"
        "Workforce & Personnel Strength: Nexura Hardware Systems is driven by a talented team of 120 full-time employees "
        "spread across our regional service centers and headquarters."
    )
    pdf1.ln(4)

    pdf1.set_font("Helvetica", "B", 11)
    pdf1.set_text_color(120, 30, 30)
    pdf1.cell(0, 7, "PAST PERFORMANCE & EXPERIENCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf1.set_font("Helvetica", "", 9)
    pdf1.set_text_color(40, 40, 40)
    pdf1.multi_cell(
        0, 5,
        "Nexura Hardware Systems has completed the following similar IT hardware supply contracts:\n"
        "  1. Order Ref MUNI/2023/41: Supply of 100 Computing Units to Municipal Corporation, Value: INR 52 Lakhs (Completed October 2023).\n"
        "  2. Order Ref POL/2024/88: Supply of 115 Commercial Laptops to State Police Department, Value: INR 60 Lakhs (Completed July 2024).\n"
        "Total completed orders: 2 orders with each order value >= INR 50 Lakhs."
    )
    doc1_path = folder / "vendor_b_company_profile.pdf"
    pdf1.output(str(doc1_path))
    print(f"Generated Vendor B Doc 1: {doc1_path}")

    # Document 2: Financials & Compliance
    pdf2 = GeMPDFBase(
        header_title="NEXURA HARDWARE SYSTEMS LTD - FINANCIAL STATEMENTS & COMPLIANCE",
        sub_title="Tender Submission: GEM/2026/B/8821941 | Statutory Financials",
        doc_code="NHS/GEM/2026/DOC-02",
    )
    pdf2.alias_nb_pages()
    pdf2.add_page()
    pdf2.set_font("Helvetica", "B", 12)
    pdf2.set_text_color(120, 30, 30)
    pdf2.cell(0, 8, "AUDITED FINANCIAL TURNOVER STATEMENT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf2.set_font("Helvetica", "", 9)
    pdf2.set_text_color(40, 40, 40)
    pdf2.multi_cell(
        0, 5,
        "As certified by our Chartered Accountant (M/s P.K. Mehta & Co., UDIN: 24087123BBBB4567), "
        "the annual turnover of Nexura Hardware Systems Ltd during the preceding three financial years is:\n"
        "  - Financial Year 2022-23: INR 0.75 Crore (INR 75 Lakhs)\n"
        "  - Financial Year 2023-24: INR 0.85 Crore (INR 85 Lakhs)\n"
        "  - Financial Year 2024-25: INR 0.95 Crore (INR 95 Lakhs)\n\n"
        "Average annual turnover of the bidder during the last three financial years is INR 0.85 Crore "
        "(Indian Rupees Eighty Five Lakhs only)."
    )
    pdf2.ln(4)

    pdf2.set_font("Helvetica", "B", 11)
    pdf2.set_text_color(120, 30, 30)
    pdf2.cell(0, 7, "STATUTORY HR & LABOUR COMPLIANCE DISCLOSURE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf2.set_font("Helvetica", "", 9)
    pdf2.set_text_color(40, 40, 40)
    pdf2.multi_cell(
        0, 5,
        "Official Statutory ESI/EPF Audit Return filing: Nexura Hardware Systems officially registers and reports "
        "a total payroll strength of 28 full-time employees as of the annual closing date of March 31, 2025."
    )
    pdf2.ln(4)

    pdf2.set_font("Helvetica", "B", 11)
    pdf2.set_text_color(120, 30, 30)
    pdf2.cell(0, 7, "STATUTORY REGISTRATION CERTIFICATES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf2.set_font("Helvetica", "", 9)
    pdf2.set_text_color(40, 40, 40)
    pdf2.multi_cell(
        0, 5,
        "1. ISO Certification: Valid ISO 9001:2015 Quality Certificate No. Q-2023-8812, valid until 20-October-2027.\n"
        "2. GST Registration: Valid GST Registration Certificate (GSTIN: 27AABCN5678K1Z2), Status: Active / Regular."
    )
    doc2_path = folder / "vendor_b_financials_and_compliance.pdf"
    pdf2.output(str(doc2_path))
    print(f"Generated Vendor B Doc 2: {doc2_path}")

    # Document 3: Technical Bid
    pdf3 = GeMPDFBase(
        header_title="NEXURA HARDWARE SYSTEMS LTD - TECHNICAL PROPOSAL",
        sub_title="Tender Submission: GEM/2026/B/8821941 | Model: Nexura UltraBook 14-Pro",
        doc_code="NHS/GEM/2026/DOC-03",
    )
    pdf3.alias_nb_pages()
    pdf3.add_page()
    pdf3.set_font("Helvetica", "B", 12)
    pdf3.set_text_color(120, 30, 30)
    pdf3.cell(0, 8, "TECHNICAL SPECIFICATIONS & HARDWARE OFFER", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf3.set_font("Helvetica", "", 9)
    pdf3.set_text_color(40, 40, 40)
    pdf3.multi_cell(
        0, 5,
        "Nexura Hardware Systems Ltd quotes our assembled / integrated enterprise laptop model "
        "'Nexura UltraBook 14-Pro' with the following technical specifications:"
    )
    pdf3.ln(3)

    specs_b = [
        ("Quoted Model", "Nexura UltraBook 14-Pro"),
        ("Processor", "Intel Core i7 13th Generation (i7-1355U, 10 cores, 12 threads, 2.4 GHz base up to 4.9 GHz boost)."),
        ("RAM / Memory", "16 GB DDR4 3200MHz RAM (expandable up to 32 GB)."),
        ("Storage (SSD)", "512 GB M.2 NVMe PCIe SSD storage."),
        ("Display Size", "14.0 inch Full HD (1920 x 1080) Anti-Glare IPS display."),
        ("Warranty", "Comprehensive on-site warranty for 3 years covering replacement of parts and power adapter."),
        ("BIS Registration", "Quoted model has valid BIS Registration under CRS scheme of MEITY (Registration No. R-41099881 conforming to IS 13252)."),
        ("Bid Validity", "Quoted rates and bid validity period is guaranteed for 90 days from the bid closing date.")
    ]
    for label, val in specs_b:
        pdf3.set_font("Helvetica", "B", 9)
        pdf3.set_text_color(30, 30, 30)
        pdf3.cell(42, 6, label + ":", border=0)
        pdf3.set_font("Helvetica", "", 9)
        pdf3.set_text_color(50, 50, 50)
        pdf3.multi_cell(0, 6, val)
        pdf3.ln(1)

    pdf3.ln(4)
    pdf3.set_font("Helvetica", "B", 10)
    pdf3.set_text_color(120, 30, 30)
    pdf3.cell(0, 6, "DECLARATION REGARDING OEM AUTHORIZATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf3.set_font("Helvetica", "", 9)
    pdf3.set_text_color(40, 40, 40)
    pdf3.multi_cell(
        0, 5,
        "Note: Nexura Hardware Systems Ltd operates as an independent third-party hardware system integrator. "
        "No OEM Authorization Letter (MAF) has been obtained or enclosed from the original component manufacturer "
        "for this specific bid reference."
    )
    doc3_path = folder / "vendor_b_technical_bid.pdf"
    pdf3.output(str(doc3_path))
    print(f"Generated Vendor B Doc 3: {doc3_path}")


def main():
    root = Path(__file__).parent
    tender_path = root / "tender_gem_2026_it_hardware.pdf"
    vendor_a_folder = root / "vendor_a"
    vendor_b_folder = root / "vendor_b"

    print("Generating demo data PDFs...")
    create_tender_pdf(tender_path)
    create_vendor_a_documents(vendor_a_folder)
    create_vendor_b_documents(vendor_b_folder)
    print("All demo data PDFs generated successfully in /demo_data!")


if __name__ == "__main__":
    main()
