"""Build the Throne Roofing GC lead workbook, CSV export and summary counts.

Usage: python3 scripts/build_leads.py
Outputs go to deliverables/.
"""
import csv
import os
import re
from collections import OrderedDict
from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import lead_data as d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables")
XLSX = os.path.join(OUT, "Throne_Roofing_GC_Leads_2026-10-08.xlsx")
CSV = os.path.join(OUT, "Throne_Roofing_Priority_Leads_2026-10-08.csv")

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")
URL_RE = re.compile(r"https?://[^\s,;)]+")


def status_bucket(status):
    s = status.upper()
    if s.startswith("OPEN"):
        return "open"
    if s.startswith("AWARDED"):
        return "awarded"
    if s.startswith("CLOSED"):
        return "closed"
    return "upcoming"  # UPCOMING, POTENTIAL, Unconfirmed


def write_sheet(wb, title, columns, rows):
    ws = wb.create_sheet(title)
    ws.append(columns)
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([r.get(c, "") if isinstance(r, dict) else r[i] for i, c in enumerate(columns)])
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            v = cell.value
            if isinstance(v, str) and v.startswith("http") and " " not in v:
                cell.hyperlink = v
                cell.font = Font(color="0563C1", underline="single")
    for i, c in enumerate(columns, 1):
        width = max(len(str(c)), *(min(len(str(ws.cell(row=r, column=i).value or "")), 60) for r in range(2, ws.max_row + 1))) if ws.max_row > 1 else len(c)
        ws.column_dimensions[get_column_letter(i)].width = max(12, min(width + 2, 60))
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    return ws


def outreach_rows():
    rows = []
    for group in (d.OUTREACH_COMPANIES, d.OUTREACH_PROJECTS):
        for (ltype, lid, name, first, last, title, email, phone, prov, status, scores, why, nxt, src) in group:
            rows.append({
                "Lead Type": ltype, "Lead ID": lid, "Company / Project": name,
                "Target Contact First Name": first, "Target Contact Last Name": last,
                "Target Contact Title": title, "Public Business Email": email, "Business Phone": phone,
                "Province": prov, "Status / Timing": status,
                "Fit Score (1-5)": scores[0], "Activity Evidence Score (1-5)": scores[1],
                "Decision-Maker Score (1-5)": scores[2], "Timing Score (1-5)": scores[3],
                "Feasibility Score (1-5)": scores[4], "Evidence Quality Score (1-5)": scores[5],
                "Total Score (/30)": sum(scores), "Why Prioritized": why, "Next Action": nxt,
                "Source URL": src, "Verification Date": d.CHECKED,
            })
    comp = sorted([r for r in rows if r["Lead Type"] == "GC company"], key=lambda r: -r["Total Score (/30)"])
    proj = sorted([r for r in rows if r["Lead Type"] == "Project"], key=lambda r: -r["Total Score (/30)"])
    for i, r in enumerate(comp, 1):
        r["Rank"] = f"C{i:02d}"
    for i, r in enumerate(proj, 1):
        r["Rank"] = f"P{i:02d}"
    return comp + proj


def source_type(url):
    host = urlparse(url).netloc.lower()
    if "linkedin.com" in host:
        return "Professional profile (LinkedIn) - not conclusive"
    gov = ("canadabuys", "purchasing.alberta", "sasktenders", "alberta.ca", "open.canada", "ouvert.canada",
           "princegeorge", "strathcona", "cityofnb", "victoriacounty", "civicinfo", "bonfirehub", "merx.com",
           "fraserhealth", "vch.ca", "infrastructureontario", "greatersudbury", "grasslands", "concordia.ab.ca",
           "bidsandtenders", "kelowna.ca", "wcb", "worksafebc", "wsib", "rbq.gouv", "oca.ca")
    if any(g in host for g in gov):
        return "Official public-sector / procurement source"
    official = ("fillmoreconstruction", "scottbuilders", "wardbros", "ledcor", "pcl.com", "everestconstruction",
                "wfgroupinc", "velcor.ca", "marshall-lee", "keller.ab.ca", "horizoncontractors", "rcabc", "arcaonline", "acsa-safety")
    if any(o in host for o in official):
        return "Official company / association website"
    news = ("on-sitemag", "renewcanada", "reminetwork", "canadianconsultingengineer", "constructconnect",
            "strathmorenow", "princegeorgecitizen", "link2build", "mydigitalpublication", "vica.arlo")
    if any(n in host for n in news):
        return "Industry publication / news"
    if any(a in host for a in ("visualping", "cleat.ai", "tenderscan", "cornerstonecontracts", "bgis.merx")):
        return "Tender aggregator / tracker (secondary)"
    return "Business directory / other secondary source"


def build_source_log(company_rows, contact_rows, project_rows, outreach, reqs):
    log = OrderedDict()

    def add(text, ref):
        for u in URL_RE.findall(str(text)):
            u = u.rstrip(".")
            log.setdefault(u, set()).add(ref)

    for r in company_rows:
        for v in r.values():
            add(v, r["Lead ID"])
    for r in contact_rows:
        for v in r:
            add(v, r[0])
    for r in project_rows:
        for v in r.values():
            add(v, r["Project ID"])
    for r in outreach:
        add(r["Source URL"], r["Rank"])
    for r in reqs:
        add(r[4], "Requirements")
    rows = []
    for i, (u, refs) in enumerate(log.items(), 1):
        stype = source_type(u)
        method = ("General reference (provincial agency) - not used as evidence for a lead" if "Requirements" in refs and len(refs) == 1
                  else "Search-engine indexed content (direct fetch blocked by environment network policy)")
        rows.append([f"S-{i:03d}", u, ", ".join(sorted(refs)), stype, method, d.CHECKED])
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    companies = d.COMPANIES
    contacts = d.CONTACTS
    projects = d.PROJECTS
    outreach = outreach_rows()

    # ---- sanity checks ----
    ids = [p["Project ID"] for p in projects]
    assert len(ids) == len(set(ids)), "duplicate project IDs"
    names = [p["Project Name"].lower() for p in projects]
    assert len(names) == len(set(names)), "duplicate project names"
    cids = [c[0] for c in contacts]
    assert len(cids) == len(set(cids)), "duplicate contact IDs"
    people = [(c[2], c[3], c[4]) for c in contacts if c[3]]
    assert len(people) == len(set(people)), "duplicate person"
    for c in contacts:
        assert len(c) == len(d.CONTACT_COLUMNS), c[0]
    for r in companies:
        assert set(r) == set(d.COMPANY_COLUMNS), r["Lead ID"]
    for p in projects:
        assert set(p) == set(d.PROJECT_COLUMNS), p["Project ID"]

    buckets = {"open": [], "upcoming": [], "awarded": [], "closed": []}
    for p in projects:
        buckets[status_bucket(p["Tender Status"])].append(p)

    wb = Workbook()
    wb.remove(wb.active)

    # ---- summary counts ----
    legacy = [p for p in projects if p["Project ID"].startswith("LEG-")]
    new = [p for p in projects if not p["Project ID"].startswith("LEG-")]
    open_verified = [p for p in buckets["open"] if "Unconfirmed" not in p["Tender Status"] and "conflicting" not in p["Tender Status"] and "scope unclear" not in p["Tender Status"] and "verify" not in p["Tender Status"]]
    open_contractor = [p for p in buckets["open"] if p["Opportunity Channel"] == d.DIRECT]
    open_consult = [p for p in buckets["open"] if p["Opportunity Channel"] == d.CONSULT]
    identified = [c for c in companies if not c["Confidence Level"].startswith("Low")]
    verified_people = [c for c in contacts if c[3] and c[14].startswith("Verified")]
    named_any = [c for c in contacts if c[3]]
    gc_emails = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\w", " ".join(c["Public Business Email"] + " " + c["Backup Business Email"] for c in companies))))
    buyer_emails = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\w", " ".join(p["Public Business Email"] for p in projects))))
    awarded_target_gc = [p for p in buckets["awarded"] if any(k in p["Confirmed General Contractor"] for k in ("LEAR", "PCL", "Ward Bros", "Ledcor", "Scott", "Fillmore"))]

    summary = [
        ["Research date", d.CHECKED],
        ["Companies researched", len(companies)],
        ["Companies confidently identified", f"{len(identified)} (Horizon Contractors Inc: identity requires verification; Rooster Building Group identified but is an envelope contractor, not a GC; WF Group matched by name only)"],
        ["Named contacts recorded", len(named_any)],
        ["Named decision-makers verified by an official or published source", f"{len(verified_people)} ({', '.join(c[3] + ' ' + c[4] for c in verified_people)}); only 1 is a Priority-1 estimating role (James Behnke, Fillmore)"],
        ["Named contacts supported by LinkedIn/directory only", len(named_any) - len(verified_people)],
        ["Verified public business emails (GC company/department inboxes)", f"{len(gc_emails)}: {', '.join(gc_emails)}"],
        ["Verified public-buyer procurement emails", f"{len(buyer_emails)}: {', '.join(buyer_emails)}"],
        ["Personal named-person emails verified", "0 (none published; none guessed)"],
        ["Unique projects/tenders in database", f"{len(projects)} ({len(legacy)} re-checked legacy leads + {len(new)} new)"],
        ["OPEN tenders (all)", f"{len(buckets['open'])} ({len(open_contractor)} roofing-contractor bids, {len(open_consult)} consultant RFPs)"],
        ["OPEN tenders with consistent official/indexed details", f"{len(open_verified)}: " + "; ".join(p['Project ID'] + ' ' + p['Project Name'][:45] for p in open_verified)],
        ["UPCOMING / POTENTIAL / Unconfirmed", len(buckets["upcoming"])],
        ["AWARDED projects with a known GC", f"{len(buckets['awarded'])} ({len(awarded_target_gc)} involve one of the 17 target GCs)"],
        ["CLOSED (kept for GC/pipeline intelligence)", len(buckets["closed"])],
        ["Best five leads to contact first", "1) City of Vernon 26-83-INF (OPEN, mandatory site visit 2026-10-14, closes 2026-11-03); 2) Jasper FireSmart Compound roof (Parks Canada, OPEN to 2026-10-22); 3) City of Prince George T26-085 ($2.45M, OPEN to ~2026-10-20); 4) LEAR Construction Management (Brooks JH, CBE envelope, Silverado); 5) Scott Builders Calgary/Edmonton (Lake Louise fire hall bidder; official bid inboxes)"],
        ["Main limitations", "Direct page fetching was blocked by the research environment's network policy, so every fact comes from search-engine indexed content of the cited URL, not a live page load. Third-party contact-data tools (ZoomInfo, Apollo, Lusha) failed to connect; Crustdata had no credit. No URL was live-tested. Most named GC contacts rest on LinkedIn snippets and must be phone-confirmed. Three legacy leads (Strathcona 26.0120, NRC M-20, VCH D424-00) could not be found in any indexed source."],
    ]
    write_sheet(wb, "Executive Summary", ["Metric", "Value"], summary)
    write_sheet(wb, "GC Companies", d.COMPANY_COLUMNS, companies)
    write_sheet(wb, "Decision-Maker Contacts", d.CONTACT_COLUMNS, contacts)
    write_sheet(wb, "Open Tenders", d.PROJECT_COLUMNS, buckets["open"])
    write_sheet(wb, "Upcoming Projects", d.PROJECT_COLUMNS, buckets["upcoming"])
    write_sheet(wb, "Awarded Projects", d.PROJECT_COLUMNS, buckets["awarded"])
    write_sheet(wb, "Closed Reference", d.PROJECT_COLUMNS, buckets["closed"])

    leg_cols = ["Project ID", "Project Name", "Tender Number", "Exists in Official Source?", "Tender Status", "Closing Date",
                "Closing Time and Time Zone", "Owner or Buyer", "Confirmed General Contractor", "Bid Route",
                "Target Estimator or Project Contact", "Public Business Email", "Business Phone", "Tender Notice URL", "Recommended Next Action", "Last Verified Date"]
    exists = {"LEG-A": "No - number not found; related Strathcona roofing RFQs found", "LEG-B": "Partly - closest PHAC roof tender found (closed)",
              "LEG-C": "Yes - capital plan + tracker; official portal not loaded", "LEG-D": "Not confirmed - only an OCA bid-calendar title",
              "LEG-E": "Yes - county website notice", "LEG-F": "No - ITT number not found", "LEG-G": "Yes - IO releases (GC procurement, not a trade tender)",
              "LEG-H": "Yes - SaskTenders RFP (number not confirmed)"}
    leg_rows = []
    for p in legacy:
        leg_rows.append({**p, "Exists in Official Source?": exists[p["Project ID"]],
                         "Bid Route": "Roofing subcontractor bids directly to owner" if p["Opportunity Channel"] == d.DIRECT else ("Approach the GC once selected" if p["Opportunity Channel"] == d.GCSUB else "Consultant RFP - roofers cannot bid; wait for construction tender")})
    write_sheet(wb, "Legacy Lead Recheck", leg_cols, leg_rows)
    write_sheet(wb, "Outreach Priority", d.OUTREACH_COLUMNS, outreach)
    write_sheet(wb, "Provincial Requirements", d.REQ_COLUMNS, d.REQUIREMENTS)
    src = build_source_log(companies, contacts, projects, outreach, d.REQUIREMENTS)
    write_sheet(wb, "Source Log", ["Source ID", "URL", "Used For (Record IDs)", "Source Type", "Access Method", "Date Checked"], src)
    wb.save(XLSX)

    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=d.OUTREACH_COLUMNS)
        w.writeheader()
        for r in outreach:
            w.writerow(r)

    for k, v in summary:
        print(f"{k}: {v}")
    print("sheets:", wb.sheetnames)
    print("sources:", len(src))


if __name__ == "__main__":
    main()
