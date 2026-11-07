"""
Builds realworld_test.csv: an independent test set of real GCC construction news
headlines, collected on 2026-10-18 after the v2 rules were frozen.

How it was collected (manual, documented): the automated RSS collector
(src/collect_rss.py) could not reach news sites from the environment this was
built in, so the items were taken from publisher listing pages and web search:

- natural_listing: every construction/real-estate article on the Gulf Construction
  "Saudi Focus"/regional section listing (Oct 2026 issue) and on TradeArabia's
  Construction & Real Estate listing (17-18 Oct 2026), excluding only navigation
  pages ("Projects at a glance", "Tenders", "Diary of events") and off-topic
  site-wide items. No item was chosen or dropped by looking at rule output, so
  this stream has a realistic share of articles with no risk event.
- targeted_search: risk-related headlines found with web searches for
  terminations, delays, payment, cost, supply-chain and regulatory news, added
  because the natural stream contains few adverse events. Stories that duplicate
  the 15 training articles (Mukaab suspension, The Line downscaling) were excluded.

Text stored is the headline plus, where the listing showed one, the publisher's
teaser (truncated). Labels are drafts by Claude and must be reviewed by the
student before being reported.
"""
import csv
from pathlib import Path

OUT = Path(__file__).with_name("realworld_test.csv")

N = "No Risk Event"
CA = "Contract Award"
MT = "Market Trend"
GCO = "Gulf Construction (gulfconstructiononline.com)"
TA = "TradeArabia"

RISK = {
    "Contract Cancellation": "Operational", "Project Suspension": "Operational", "Project Delay": "Operational",
    "Supply Chain Disruption": "Operational", "Workforce Change": "Operational", "Cost Overrun": "Financial",
    "Payment Risk": "Financial", "Financial Result": "Financial", "Regulatory Change": "Regulatory",
    CA: "Market", MT: "Market", N: "None",
}


def g(title, art_id, ev=N, sev="None", amb="", note=""):
    return dict(title=title, teaser="", publisher=GCO, url=f"https://www.gulfconstructiononline.com/Article/{art_id}",
                publication_date="2026-10", sampling="natural_listing", gold_event_type=ev, gold_severity=sev,
                ambiguous=amb, note=note)


def t(title, art_id, teaser, date, ev=N, sev="None", amb="", note=""):
    return dict(title=title, teaser=teaser, publisher=TA, url=f"https://www.tradearabia.com/News/{art_id}",
                publication_date=date, sampling="natural_listing", gold_event_type=ev, gold_severity=sev,
                ambiguous=amb, note=note)


def s(title, pub, url, teaser, date, ev, sev, amb="", note=""):
    return dict(title=title, teaser=teaser, publisher=pub, url=url, publication_date=date, sampling="targeted_search",
                gold_event_type=ev, gold_severity=sev, ambiguous=amb, note=note)


ROWS = [
    g("Capital’s construction boom enters delivery and discipline phase", 487091),
    g("Expo 2030 Riyadh enters vertical build phase; JV to set up residential community", 487098),
    g("Cliff-edge stadium takes shape at Qiddiya", 487101),
    g("Qiddiya circuit on track as 20-storey ‘Blade’ corner rises", 487102),
    g("Diriyah’s second-stage districts progress", 487103),
    g("OSUS Eye to bring ‘10-Minute City’ to North Riyadh", 487104),
    g("QDC prepares for Saudi Arabia’s next growth wave", 487113),
    g("TYF rolls out rebar mesh welder", 487114),
    g("Nordimpianti acquires Echo Precast Engineering", 487116, note="M&A is outside the event taxonomy"),
    g("Qatar eyes $61 billion infrastructure, real estate investments", 487119, MT, "Low"),
    g("Statetron advances plans for next-gen industrial campus", 487120),
    g("Parsons targets Qatar’s next phase of infrastructure growth", 487122),
    g("Wider role for Parsons on Lusail infrastructure", 487123, CA, "Low", "yes",
      "expanded scope implies a contract award; headline does not say so"),
    g("Beyond the block: lessons from The Pearl-Qatar", 487124),
    g("JLH-02 boosts LogiPoint’s controlled-ambient network", 487127),
    g("UAE bolsters logistics to back construction pipeline", 487128),
    g("Sumea opens global trade hub in Jafza", 487129),
    g("HUMAIN and DataVolt break ground on Oxagon AI data centre", 487132),
    g("Smart cooling key to data centre expansion: Grundfos", 487134),
    g("Why cooling resilience starts with early leak detection", 487136),
    g("Why giga-projects fail, and how disciplined coordination saves them", 487148,
      note="opinion piece, no specific event"),
    g("Geberit BIM plug-in evolves into digital planning tool", 487150),
    g("From scan to BIM: Mapping Dubai’s metro future", 487152),
    g("Tadano targets Middle East jobsites with crawler aerial work platforms", 487155),
    g("Wolffkran powers twin bridge expansion project in Riyadh", 487157),
    g("XCMG rolls out first unit of 14,000-ton ring crane", 487158),
    g("Grove boosts Kuwait presence, powers Turkish fleet renewal", 487160),
    g("Raimondi expands T Series with lightweight flat-top model", 487162),
    g("Why construction projects almost always go over budget", 487168,
      note="explainer on overruns in general, no specific event"),
    g("Pay-when-paid clauses face fresh curbs", 487170, "Regulatory Change", "Low"),
    g("VA Group to develop Muttrah waterfront", 487174),
    g("Moon World Resorts appoints cost consultant", 487208, CA, "Low", "yes",
      "consultant appointment treated as a contract award"),
    g("Heisco wins $359m EPC contract for KOC facilities", 487209, CA, "Low"),
    g("Oman-UAE rail link set for trials in late 2027", 487210, note="schedule update, no delay reported"),
    g("ICCP to launch protocol to manage claims", 487211, note="industry protocol, not regulation"),
    g("Al Mouj Muscat delivers four Business Park buildings", 487212),
    g("Bilfinger wins FEED deal for Oman fuels project", 487213, CA, "Low"),
    g("Megha Engineering lands $379m KOC contract", 487214, CA, "Low"),
    g("Mace drives delivery of Oman’s cultural complex", 487215),
    g("Consultants sought for 3,000 MW solar projects", 487216, note="tender stage, no award"),
    g("ALUPCO expands solutions portfolio with Al Hilal Stonework partnership", 487175),
    g("ROSHN, Talaat Moustafa to develop Riyadh community", 487218,
      note="development partnership, not a construction contract"),
    g("Garuda unit wins Jeddah twisting tower deal", 487219, CA, "Low"),
    g("PIF unveils new destination on Al-Khafji coast", 487221),
    g("Almajdiah, Capital Hill seal deal for KEC residences", 487222, CA, "Low", "yes",
      "'deal' could be a development agreement rather than a construction contract"),
    g("Samsung E&A secures $3.46bn Sabic EPC work", 487223, CA, "Low"),
    g("Construction costs up 2.3pc in August, says report", 487224, MT, "Medium",
      note="sector-wide cost index, not a project overrun"),
    g("Binladin achieves safety milestone at record-setting Jeddah Tower site", 487225),
    g("WSP lands design contract for King Fahd airport", 487227, CA, "Low"),
    g("Umm Al Qura, Numu ink deal to build Makkah tower", 487230, CA, "Low"),
    g("Hassan Allam unit wins Al Khobar leisure complex work", 487232, CA, "Low"),
    g("RSG launches giant off-grid renewable energy system", 487235),
    g("KAFD opens 214-key Atheel hotel", 487237),
    g("AMD, PIF unit to set up $10bn AI powerhouse", 487239),
    g("NCP qualifies six bidders for Qassim airport PPP", 487240, note="tender stage, no award"),
    g("4,310-sq-km nature reserve near Riyadh gets go-ahead", 487241),
    g("Al Akaria awards PMC work for Porta Jeddah", 487242, CA, "Low"),
    g("Zayed Waterfront masterplan unveiled", 487177),
    g("Dubai approves first phase of 80-km road corridor", 487244, note="project approval"),
    g("Meraas awards contract for City Walk Crestlane", 487245, CA, "Low"),
    g("Etihad Rail launches Dubai passenger service", 487249),
    g("Miral unveils $3.3bn Yas Island project pipeline", 487251),
    g("Lamprell group secures offshore project deal", 487252, CA, "Low"),
    g("Aldar launches 351-unit villa community development at Saadiyat Island", 487254),
    g("Fakhruddin unveils 463-unit mixed-use project", 487255),
    g("Dubai Holding awards deal for $1.36bn HQ, residences", 487257, CA, "Low"),
    g("Ramada branded homes break ground in Dubai", 487259),
    g("DHCC launches work on Dubai Creek Gardens", 487261),
    g("Nakheel awards contract for Bay Grove Residences", 487269, CA, "Low"),
    g("Damac completes 50,000 residences handover; inks $2.72bn deals in H1", 487270, "Financial Result", "Low",
      "yes", "half-year sales figure; could also be read as no event"),
    g("Dugasta unveils two residential projects", 487272),
    g("Nature-led community to rise at Dubai Water Canal", 487274),
    g("Final phase of Bloom Living launched", 487275),
    g("Second phase of Radisson homes unveiled at Reem", 487276),
    g("Wynn Al Marjan to get Mayfair, Paris luxury homes", 487277),
    g("Azizi unveils $8.1bn Sharjah community", 487349),
    g("Big 5 Construct Saudi helps set up new connections, collaborations", 487178),
    g("Dubai takes centre stage in global coatings ecosystem", 487282),
    g("Alba set for debut ‘Made in GCC’ expo in Bahrain", 487287),
    g("Saudi Arabia’s $1.6 trn boom puts geotechnical engineering in focus", 487288),
    g("Saudi Arabia spearheading $90bn hotel pipeline", 487290, MT, "Low"),

    t("Dubai's real estate investments hit $185bn in 2025, says report", 488178,
      "The value of Dubai's real estate investments has grown steadily over the past few years, rising nearly five-fold from...",
      "2026-10-18", MT, "Low"),
    t("GCC industrial investments hit $426bn across nearly 22,000 factories", 488176,
      "The GCC countries have built an investment base of $426 billion across nearly 22,000 factories,...",
      "2026-10-18", MT, "Low"),
    t("Dubai International Project Management Forum to kick off in January", 488175,
      "Global business leaders, government officials, project management specialists from across the globe will be at...",
      "2026-10-18"),
    t("Armah inks land lease agreement to develop sports club in Riyadh", 488170,
      "Saudi-based Armah Sports Company (Armah) has signed a land lease agreement with Fawaz Abdulmohsen Saad Bin Saeed...",
      "2026-10-18"),
    t("Top construction expos Saudi Build, Elenex postponed to next year", 488166,
      "Two of the major events in the Saudi construction sector - the 36th edition of Saudi Build and the 27th edition...",
      "2026-10-18", amb="yes", note="a trade show postponement, not a construction project delay"),
    t("IREIS 2026 returns to Abu Dhabi as real estate transactions top $48bn", 488160,
      "The International Real Estate and Investment Show (IREIS) 2026 will be back in Abu Dhabi next month bringing together...",
      "2026-10-18", note="event announcement"),
    t("Gulf Spic lowest bidder for KOC booster stations enhancement project", 488145,
      "Kuwait Oil Company (KOC) has announced that Gulf Spic General Trading & Contracting, a leading Kuwaiti firm specialised...",
      "2026-10-17", note="lowest bidder, not yet awarded"),
    t("Bahrain's key irrigation project on track for year-end completion", 488144,
      "Bahraini authorities said steady progress was being made on the new agricultural project in Buri with nearly 87%...",
      "2026-10-17"),
    t("19 firms in race for Madinat Salman community development projects", 488093, "", "2026-10", note="tender stage"),
    t("Moma marks key construction milestone at Dubai beachfront property", 487935, "", "2026-10"),
    t("Ohana launches second phase of Manchester City branded homes in Abu Dhabi", 487864, "", "2026-10"),
    t("Samana enters premium lifestyle property market with new brand", 488115, "", "2026-10"),

    s("Trojena terminates Ski Village steel structure contract", "MEED",
      "https://guest.meed.com/trojena-terminates-ski-village-steel-structure-contract/", "", "",
      "Contract Cancellation", "High"),
    s("Neom terminates $5bn Trojena dams contract with Webuild", "MEED",
      "https://guest.meed.com/neom-terminates-5bn-trojena-dams-contract-with-webuild/", "", "",
      "Contract Cancellation", "High"),
    s("GCC sheds $27bn as project completions outpace awards", "MEED Mashreq Industry Insight",
      "https://www.meedmashreqindustryinsight.com/?p=5236", "", "", MT, "Medium"),
    s("Shelved gigaprojects + regional conflict weigh on 1Q 2026 Saudi project contract awards", "Enterprise",
      "https://enterpriseam.com/ksa/2026/04/30/shelved-gigaprojects-regional-conflict-weigh-on-1q-2026-saudi-project-contract-awards/",
      "Saudi project contract awards fell to their second-lowest quarterly level in more than five years in 1Q 2026",
      "2026-04-30", MT, "Medium"),
    s("Wynn Resorts pushes back opening of UAE resort to Sept. 2027, increases budget by $600M", "CDC Gaming",
      "https://cdcgaming.com/wynn-resorts-pushes-back-opening-of-al-marjan-resort-to-sept-2027-increases-budget-by-600-million/",
      "Wynn Resorts announced that the opening of its $5 billion-plus Wynn Al Marjan Island casino resort",
      "2026-08-04", "Cost Overrun", "High", "yes",
      "headline reports both a delay and a budget increase; cost chosen as primary"),
    s("Emaar delays Dubai Creek Tower tender over cost issues", "AGBI",
      "https://www.agbi.com/construction/2026/06/emaar-delays-dubai-creek-tower-tender-over-cost-issues/",
      "Emaar Properties has reportedly pushed back the issuance of the tender for Dubai Creek Tower by at least four months.",
      "2026-06", "Project Delay", "Medium", note="headline taken from the URL; page showed no headline"),
    s("Gulf contractors face post-war materials squeeze", "MEED",
      "https://www.meed.com/gulf-contractors-face-post-war-materials-squeeze", "", "",
      "Supply Chain Disruption", "Medium"),
    s("UAE developers weather Hormuz disruption as contractors absorb rising costs, says Moody's", "Khaleej Times",
      "https://www.khaleejtimes.com/business/uae-developers-weather-hormuz-disruption-as-contractors-absorb-rising-costs-says-moodys",
      "UAE real estate developers are managing the fallout from ongoing disruption to shipping through the Strait of Hormuz better",
      "2026-07-01", "Supply Chain Disruption", "Medium"),
    s("Saudi authorities tighten rules for contracting firms to ensure quality", "Arab News",
      "https://arab.news/gw5sc", "", "", "Regulatory Change", "Medium"),
    s("Saudi Arabia downscales flagship Red Sea giga-project", "The New Arab",
      "https://www.newarab.com/news/saudi-arabia-downscales-flagship-red-sea-giga-project", "", "2026-02",
      "Project Suspension", "High"),
    s("Projects market: Capacity crunch triggers slowdown", "MEED",
      "https://www.meed.com/projects-market-capacity-crunch-triggers-slowdown/", "", "", MT, "Medium", "yes",
      "capacity crunch could also be read as a workforce constraint"),
    s("Gulf construction stays resilient as conflict weighs on real estate: report", "TradeArabia",
      "https://tradearabia.com/News/465461/Gulf-construction-stays-resilient-as-conflict-weighs-on-real-estate-report",
      "", "", MT, "Low"),
    s("Construction sector remains resilient despite rising costs: AESG report", GCO,
      "https://gulfconstructiononline.com/Article/464354/Construction_sector_remains_resilient_despite_rising_costs_AESG_report",
      "", "", MT, "Low"),
    s("Rising costs squeeze UAE real estate margins", "AGBI",
      "https://www.agbi.com/real-estate/2026/07/rising-costs-squeeze-uae-real-estate-margins/",
      "Profitability in the UAE real estate sector is being squeezed by a combination of rising material costs,",
      "2026-07", MT, "Medium", note="headline taken from the URL; sector-wide costs, not a project overrun"),
    s("Middle East conflict: Impact and way forward for construction, real estate", GCO,
      "https://gulfconstructiononline.com/Article/390689/Middle_East_conflict_Impact_and_way_forward_for_construction,_real_estate",
      "", "", "Supply Chain Disruption", "Medium", "yes", "analysis piece; headline does not name the specific impact"),
]

COLS = ["case_id", "title", "teaser", "publisher", "url", "publication_date", "collected_date", "sampling",
        "gold_event_type", "gold_risk_category", "gold_severity", "ambiguous", "note", "annotator"]

if __name__ == "__main__":
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for i, row in enumerate(ROWS, 1):
            row.update(case_id=f"R{i:03d}", collected_date="2026-10-18",
                       gold_risk_category=RISK[row["gold_event_type"]],
                       annotator="claude-draft (needs Rini's review)")
            w.writerow(row)
    print(f"{len(ROWS)} rows -> {OUT.name}")
