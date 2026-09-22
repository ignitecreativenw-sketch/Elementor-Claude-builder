#!/usr/bin/env python3
"""
Populate Yoast titles and meta descriptions for every page and post.

  WP_URL=... WP_USER=... WP_APP_PASSWORD=... python3 deploy/push_seo.py
  python3 deploy/push_seo.py --check     # report what is live, write nothing

REQUIRES deploy/mu-plugins/teb-site-fixes.php to be installed first. Yoast does
not register its meta for REST, so without that plugin every write here is
accepted with a 200 and silently dropped — which is exactly what happened when
this was first attempted. The script verifies the write took and says so.

Descriptions are written to be read by a human in a search result: what the
page is for and what happens next, inside Google's ~155 character display
limit. Nothing here states a rate, an LTV or a lending criterion.
"""
import importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sm", os.path.join(HERE, "sync_media.py"))
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)

CHECK = "--check" in sys.argv
SUFFIX = " | The Expert Broker"

# slug -> (yoast title, meta description)
PAGES = {
    "home-new": (
        "Mortgage Advice for Landlords & Homeowners" + SUFFIX,
        "Whole of market mortgage advice from complex limited company buy to "
        "lets to a straightforward residential move. Free initial "
        "consultation, no obligation."),
    "about": (
        "About Us — Over 20 Years of Mortgage Experience" + SUFFIX,
        "Honest, transparent mortgage advice from a broker trusted by "
        "landlords for over two decades. Nominated at the British Specialist "
        "Lending Awards 2022."),
    "services": (
        "Our Mortgage Services" + SUFFIX,
        "Buy to let, residential, limited company, HMO, multi-unit, "
        "commercial and bridging finance — arranged with whole of market "
        "access. Free initial consultation."),
    "contact": (
        "Contact Us — Speak to a Mortgage Broker" + SUFFIX,
        "Tell us what you need and Steve will call you back, usually the same "
        "working day. Your initial consultation is free of charge and without "
        "obligation."),
    "blog": (
        "Mortgage Insight for Landlords & Homeowners" + SUFFIX,
        "Plain-English notes on buy to let, limited company structures, HMOs "
        "and bridging finance — written for landlords and homeowners, not for "
        "other brokers."),
    "case-studies": (
        "Case Studies — Complex Mortgages, Solved" + SUFFIX,
        "Real cases: portfolio landlords, limited company structures, "
        "bridging and complex income. How each one was structured and which "
        "lender said yes."),

    # service pages
    "buy-to-let": (
        "Buy to Let Mortgages for Landlords" + SUFFIX,
        "Whole of market buy to let mortgage advice for landlords, from a "
        "first rental property to a full portfolio. Free initial "
        "consultation, no obligation."),
    "residential": (
        "Residential Mortgages" + SUFFIX,
        "First time buyer or coming to the end of a fixed rate? Whole of "
        "market residential mortgage advice, with a free initial "
        "consultation and no obligation."),
    "limited-company-buy-to-let": (
        "Limited Company Buy to Let Mortgages" + SUFFIX,
        "Mortgages for landlords holding property through a limited company. "
        "Specialist lenders, personal guarantees and structure explained in "
        "plain English."),
    "hmos": (
        "HMO Mortgages for Student & Professional Lets" + SUFFIX,
        "Specialist HMO mortgage advice for student and professional houses "
        "in multiple occupation. Whole of market access and a free initial "
        "consultation."),
    "multi-unit-mufb": (
        "Multi-Unit Freehold Block (MUFB) Mortgages" + SUFFIX,
        "Specialist finance for multiple flats under one freehold title. "
        "Whole of market access for portfolio landlords, with a free initial "
        "consultation."),
    "commercial-and-semi-commercial": (
        "Commercial & Semi-Commercial Mortgages" + SUFFIX,
        "Office blocks, retail units and mixed-use premises, purchase or "
        "remortgage. Specialist commercial mortgage advice with a free "
        "initial consultation."),
    "bridging-finance": (
        "Bridging Finance for Auction & Refurbishment" + SUFFIX,
        "Short-term finance for auction purchases and refurbishment projects, "
        "arranged quickly. We look at the exit first. Free initial "
        "consultation, no obligation."),

    # case studies
    "london-portfolio": (
        "Case Study: £9m for a London Portfolio Landlord" + SUFFIX,
        "How a limited company portfolio landlord in London secured £9m of "
        "borrowing, and the lender structure that made it work."),
    "bridging-holiday-let": (
        "Case Study: £1.3m Bridging for a Holiday Let" + SUFFIX,
        "A £1.3m bridging facility for a holiday let acquisition and "
        "refurbishment — how the deal was structured and how it exited."),
    "complex-income": (
        "Case Study: Complex Income, Offer in Three Days" + SUFFIX,
        "A borrower with complex income turned down elsewhere, with a formal "
        "mortgage offer in three working days."),
}

# blog posts, by slug
POSTS = {
    "first-rental-property-what-lenders-look-at": (
        "What Lenders Look At on a First Buy to Let" + SUFFIX,
        "A lender judging a buy to let asks whether the property pays for "
        "itself before it asks about your salary. What that means in "
        "practice."),
    "personal-name-or-limited-company": (
        "Personal Name or Limited Company?" + SUFFIX,
        "The structure decision is a tax question with a lending "
        "consequence. What changes on the borrowing side, and the order to "
        "make the decision in."),
    "when-bridging-finance-is-the-right-tool": (
        "When Bridging Finance Is the Right Tool" + SUFFIX,
        "Short-term finance solves a narrow set of problems well. The exit is "
        "the whole deal — how to tell whether yours stands up."),
}


def apply(kind, endpoint, ids, table):
    ok = dropped = missing = 0
    for slug, (title, desc) in table.items():
        pid = ids.get(slug)
        if not pid:
            print(f"   ?  {slug:38s} no id — skipped")
            missing += 1
            continue
        if len(desc) > 160:
            print(f"   !  {slug:38s} description is {len(desc)} chars")
        if CHECK:
            cur = sm.call("GET", f"/wp/v2/{endpoint}/{pid}?context=edit&_fields=meta")
            have = (cur.get("meta") or {}).get("_yoast_wpseo_metadesc", "")
            print(f"   {'set' if have else '---':>4}  {slug:38s} {have[:48]}")
            continue
        r = sm.call("POST", f"/wp/v2/{endpoint}/{pid}", body={"meta": {
            "_yoast_wpseo_title": title,
            "_yoast_wpseo_metadesc": desc,
        }})
        back = (r.get("meta") or {}).get("_yoast_wpseo_metadesc")
        if back:
            print(f"   +  {slug:38s} {len(desc):3d} chars")
            ok += 1
        else:
            print(f"   x  {slug:38s} WRITE DROPPED — mu-plugin not installed?")
            dropped += 1
    return ok, dropped, missing


def main():
    pages = json.load(open(os.path.join(HERE, "pages.json")))
    posts = {p["slug"]: p["id"] for p in
             sm.call("GET", "/wp/v2/posts?per_page=100&status=any&_fields=id,slug")}

    print("==> pages")
    a = apply("page", "pages", pages, PAGES)
    print("==> posts")
    b = apply("post", "posts", posts, POSTS)

    if CHECK:
        return 0
    ok, dropped, missing = (a[0] + b[0], a[1] + b[1], a[2] + b[2])
    print(f"\n{ok} written, {dropped} dropped, {missing} without an id")
    if dropped:
        print("Writes were accepted and discarded. Yoast's meta is not "
              "registered for REST — install deploy/mu-plugins/teb-site-fixes.php "
              "and run this again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
