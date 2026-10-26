"""
Utility to generate a realistic sample IT Hardware tender PDF (Laptop Procurement)
for testing TenderCheck PDF text extraction and requirement extraction.
"""
from pathlib import Path
from fpdf import FPDF


class TenderPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "GOVERNMENT E-MARKETPLACE (GeM) - BID DOCUMENT", ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "Bid Reference: GEM/2026/B/8821941 | Directorate of Information Technology", ln=True, align="C")
        self.line(10, 24, 200, 24)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Tender Reference: GEM/2026/B/8821941", align="C")


def generate_sample_it_hardware_tender(output_path: Path) -> Path:
    """
    Generate a 3-page sample IT hardware tender PDF covering 10-12 distinct requirements:
      1. Minimum average annual turnover (INR 1.5 Crore)
      2. Years of experience (min 3 years in IT hardware supply)
      3. Similar past orders (minimum 2 completed orders for laptops)
      4. Warranty (minimum 3 years on-site comprehensive OEM warranty)
      5. RAM (minimum 16 GB DDR4/DDR5)
      6. SSD (minimum 512 GB NVMe SSD)
      7. Processor (Intel Core i7 13th Gen or higher)
      8. Display size (minimum 14.0 inch FHD)
      9. Certifications (ISO 9001:2015)
      10. Regulatory compliance (BIS registration under CRS)
      11. OEM Authorization letter (MAF)
      12. Make in India local content (Class I / Class II)
      13. MSME/Startup exemption clause
      14. Bid validity (90 days)
    """
    pdf = TenderPDF()
    pdf.alias_nb_pages()

    # --- Page 1: General Info & Financial / Experience Eligibility ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "SECTION I: INVITATION FOR BIDS & ELIGIBILITY CRITERIA", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "1. Scope of Work:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        "Supply, installation, testing, and 3-year on-site comprehensive warranty support "
        "of 120 units of Commercial Enterprise Grade Laptops for government administrative offices."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "2. Financial Criteria:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        "2.1 Minimum Average Annual Turnover: The average annual turnover of the bidder during the last "
        "three financial years (FY 2022-23, 2023-24, and 2024-25) must be at least INR 1.50 Crore "
        "(Indian Rupees One Crore Fifty Lakhs only). A CA certificate with UDIN must be enclosed."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "3. Experience & Past Performance:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        "3.1 Years in Business: The bidder must have at least 3 years of experience in the supply and "
        "maintenance of IT hardware and computer systems to Central/State Govt departments or PSUs.\n"
        "3.2 Past Similar Orders: The bidder must have completed at least 2 similar orders for supply of "
        "laptops or computing equipment in the preceding 3 years, with each order value not less than INR 50 Lakhs."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "4. MSME & Startup Policy Exemption:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        "4.1 Relaxation of Norms: In line with GeM Public Procurement Policy, Micro and Small Enterprises "
        "(MSEs) and DPIIT-recognized Startups are exempted from the requirements of prior turnover and prior "
        "experience, subject to meeting technical quality specifications."
    )

    # --- Page 2: Technical Specifications ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "SECTION II: TECHNICAL SPECIFICATIONS FOR LAPTOPS", ln=True)
    pdf.ln(2)

    specs = [
        ("Processor", "Intel Core i7 13th Generation or equivalent 10-core/12-core processor (min 2.4 GHz base)."),
        ("RAM / Memory", "Minimum 16 GB DDR4/DDR5 3200MHz RAM, upgradable to at least 32 GB."),
        ("Storage (SSD)", "Minimum 512 GB M.2 NVMe PCIe Gen 4 SSD storage."),
        ("Display Size", "Minimum 14.0 inch Full HD (1920 x 1080) Anti-Glare IPS display with 250 nits brightness."),
        ("Operating System", "Pre-installed Windows 11 Professional 64-bit with OEM recovery partition."),
        ("Warranty", "Minimum 3 years comprehensive on-site OEM warranty including battery and power adapter."),
        ("Battery", "Minimum 50 Wh lithium-ion battery supporting fast charge (up to 80% in 60 mins)."),
    ]

    for title, desc in specs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 6, title + ":", border=0)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 6, desc)
        pdf.ln(1)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "5. Warranty & Service Level Agreement:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0, 5,
        "The bidder/OEM must guarantee comprehensive on-site warranty for a minimum period of 3 years "
        "from the date of successful commissioning. Any defect must be resolved within 48 hours."
    )

    # --- Page 3: Mandatory Certifications, Compliance & Validity ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "SECTION III: MANDATORY CERTIFICATES & COMPLIANCE", ln=True)
    pdf.ln(2)

    certs = [
        ("ISO Certification", "The OEM and the Bidder must possess a valid ISO 9001:2015 quality certificate."),
        ("GST Registration", "The bidder must submit a valid GST Registration Certificate along with active status."),
        ("BIS Registration", "The quoted laptop model must have valid BIS Registration under the CRS scheme of MEITY (IS 13252)."),
        ("OEM Authorization", "Bidders who are not OEMs must submit an authentic OEM Authorization Letter (MAF) issued specifically for Bid GEM/2026/B/8821941."),
        ("Make in India (MII)", "Purchase preference will be given to Class I Local Suppliers (local content >= 50%) and Class II Local Suppliers (local content >= 20%) under PPP-MII policy."),
        ("Bid Validity", "The quoted rates and bid shall remain valid for a minimum of 90 days from the bid submission closing date.")
    ]

    for item, text in certs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, item + ":", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, text)
        pdf.ln(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path


if __name__ == "__main__":
    out = Path("sample_tender.pdf")
    generate_sample_it_hardware_tender(out)
    print(f"Sample tender PDF generated at: {out.resolve()}")
