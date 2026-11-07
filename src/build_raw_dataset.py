"""
Phase 1 - raw dataset seed.
Articles below are original paraphrased summaries (not copied text) of real,
dated GCC/Saudi construction & infrastructure news stories collected on
2026-08-06, with the source URL kept for traceability. Matches the project's
article_id/title/article_text/publication_date/publisher/url/category schema.
"""
import pandas as pd

from config import RAW_CSV

articles = [
    dict(article_id=1, title="Riyadh cube skyscraper construction suspended amid financing review",
         article_text="Saudi Arabia has paused construction of the Mukaab, the cube-shaped tower at the heart of the New Murabba development in Riyadh, while authorities reassess the project's financing and feasibility. The pause is part of a wider recalibration of Vision 2030 giga-projects as the kingdom's sovereign wealth fund manages costs and reprioritises spending toward Expo 2030 and World Cup 2034 infrastructure.",
         publication_date="2026-01-28", publisher="The Arab Weekly", url="https://thearabweekly.com/saudi-arabia-suspends-work-riyadh-skyscraper-it-reassesses-mega-projects", category="construction"),
    dict(article_id=2, title="NEOM cancels tunnel contract with Hyundai-Samsung consortium",
         article_text="NEOM has terminated a tunnel construction contract that had been awarded to a joint venture led by Hyundai Engineering & Construction with Samsung C&T, following a breakdown in contract-term negotiations. The cancellation is one of several NEOM contract terminations this year as the giga-project scales back construction activity.",
         publication_date="2026-04-08", publisher="Construction Week Online", url="https://www.constructionweekonline.com/gigaprojects/saudi-gigaprojects-neom", category="construction"),
    dict(article_id=3, title="The Line downscaled after cost overruns and delays",
         article_text="NEOM's The Line megacity is being significantly downscaled after its budget ballooned past $500 billion and construction fell years behind the original 2030 completion target. Officials now expect the development to house far fewer residents than originally planned, with only a small fraction of the 170km structure under active construction.",
         publication_date="2026-01-28", publisher="Construction Digital", url="https://constructiondigital.com/news/why-is-saudi-slowing-neom-its-1-5tn-construction-project", category="construction"),
    dict(article_id=4, title="Alec unit wins $500m EPC contracts across the GCC",
         article_text="Target Engineering Construction Company, a subsidiary of Dubai-based Alec Holdings, has been awarded three engineering, procurement and construction contracts across the GCC worth a combined $500 million, with completion timelines of 10 to 21 and 36 months. Alec reported first-quarter net profit of AED230 million, up sharply year on year, on an 87% rise in revenue.",
         publication_date="2026-06-08", publisher="AGBI", url="https://www.agbi.com/construction/2026/06/alec-unit-wins-500m-gcc-construction-contracts/", category="finance"),
    dict(article_id=5, title="Al Yamama awarded Expo 2030 Riyadh infrastructure package",
         article_text="Al Yamama Company has been awarded the main utilities and infrastructure works contract for Expo 2030 Riyadh, while Eversendai separately secured a $299.5 million structural steel contract from Azizi Developments, underscoring continued contract-award momentum in the kingdom despite the wider giga-project recalibration.",
         publication_date="2026-04-22", publisher="SaudiGulf Projects", url="https://www.saudigulfprojects.com/2026/04/weatherford-announce-major-contracts-awards-across-gcc/", category="construction"),
    dict(article_id=6, title="GCC project awards jump 30% in Q2 2026 led by Saudi Arabia",
         article_text="GCC project awards totalled $59.4 billion in the second quarter of 2026, up 30% year on year, according to Kamco Invest's quarterly projects market report. Saudi Arabia retook the lead with $30 billion in awards, up over 150% quarter on quarter, while Qatar's awards fell sharply and the UAE also declined year on year.",
         publication_date="2026-08-01", publisher="Emile Construction", url="https://www.emilecon.com/post/gcc-project-awards-q2-2026", category="market"),
    dict(article_id=7, title="Iran conflict disrupts Saudi construction supply chains via Strait of Hormuz",
         article_text="The eruption of the Iran-US-Israel conflict in late February 2026 disrupted shipping through the Strait of Hormuz, adding supply-chain paralysis and cost escalation on top of an already tightening fiscal environment for Saudi construction. Legal advisers report the disruption has deepened termination disputes, performance-bond exposure and cost claims tied to the earlier giga-project recalibration.",
         publication_date="2026-06-04", publisher="Chambers and Partners", url="https://practiceguides.chambers.com/practice-guides/construction-law-2026/saudi-arabia/trends-and-developments", category="regulatory"),
    dict(article_id=8, title="Saudi regulators tighten permit enforcement, causing post-mobilisation delays",
         article_text="Stricter enforcement of zoning, safety and environmental permitting in 2026 is causing Saudi construction projects to be delayed after mobilisation when permits are withheld or revoked, creating cost exposure and contractual disputes between contractors and employers. Legal advisers are recommending pre-acquisition regulatory reviews and permit-responsibility matrices to manage the risk.",
         publication_date="2026-02-16", publisher="Atyar Law Company", url="https://al-tayyar.com.sa/en/critical-challenges-in-construction-saudi-arabia/", category="regulatory"),
    dict(article_id=9, title="PIF warns Saudi construction boom is outpacing domestic manufacturing",
         article_text="Saudi Arabia's Public Investment Fund has warned that the kingdom's construction boom is proceeding without a sufficiently developed domestic manufacturing base, and is pushing to accelerate the build-out of local factories to reduce reliance on imported materials.",
         publication_date="2026-02-10", publisher="MEXC News", url="https://www.mexc.com/it-IT/news/679487", category="operational"),
    dict(article_id=10, title="NEOM relocates staff and cuts workforce to control mega-project costs",
         article_text="NEOM has been relocating more than 1,000 employees to Riyadh and reducing headcount to control costs and tighten oversight of its giga-project portfolio, part of a broader pattern of budget-driven scale-backs across Vision 2030 developments including the postponement of the 2029 Asian Winter Games at Trojena.",
         publication_date="2026-01-28", publisher="The Arab Weekly", url="https://thearabweekly.com/saudi-arabia-suspends-work-riyadh-skyscraper-it-reassesses-mega-projects", category="operational"),
    dict(article_id=11, title="Saudi construction sector undergoing fiscal recalibration, Chambers guide finds",
         article_text="Saudi Arabia's construction sector is undergoing a period of transformation driven by two compounding developments: a strategic re-scoping and, in some cases, cancellation of flagship Vision 2030 projects, and the shipping disruption from the Iran conflict, which together have deepened termination disputes, bond exposure and cost claims across the industry.",
         publication_date="2026-06-04", publisher="Chambers and Partners", url="https://practiceguides.chambers.com/practice-guides/construction-law-2026/saudi-arabia/trends-and-developments", category="financial"),
    dict(article_id=12, title="Milestone and indexation clauses used to manage Saudi construction payment risk",
         article_text="Saudi construction contracts commonly use milestone-based payments and price indexation clauses to manage the risk of late payment and price fluctuation, with advanced and delayed payment provisions used to allocate cash-flow risk between contractors and employers, according to a legal market guide.",
         publication_date="2026-06-04", publisher="Chambers and Partners", url="https://practiceguides.chambers.com/practice-guides/construction-law-2026/saudi-arabia/trends-and-developments", category="financial"),
    dict(article_id=13, title="GCC buildings contractor awards projected to climb in 2026 despite payment stretch",
         article_text="GCC MEP contractor awards are projected to climb further in 2026, with the UAE and Saudi Arabia driving most of the activity, even as payment cycles stretch and copper and switchgear lead times squeeze HVAC procurement amid structurally short skilled labour supply.",
         publication_date="2026-07-23", publisher="Ventures Onsite", url="https://www.venturesonsite.com/gcc-mep-industry-report", category="market"),
    dict(article_id=14, title="Qiddiya entertainment city launch delayed by three days",
         article_text="Saudi Arabia delayed by three days the ceremonial launch of construction at Qiddiya, the 334-square-kilometre entertainment, sports and cultural project southwest of Riyadh, with the first development phase originally targeted for completion in 2022.",
         publication_date="2018-04-26", publisher="Gulf News", url="https://www.pressreader.com/uae/gulf-news/20180426/281844349243535", category="construction"),
    dict(article_id=15, title="Engineering assessment questions feasibility of The Line's construction pace",
         article_text="An independent engineering assessment found that completing The Line by its stated 2030 deadline would require construction at roughly 15,000 times the typical rate of a UK project, calling the original timeline unrealistic given satellite-confirmed progress of only a small fraction of the full 170km structure.",
         publication_date="2026-01-02", publisher="Newsweek", url="https://www.newsweek.com/how-saudi-arabias-futuristic-megacity-will-progress-in-2026-11244377", category="construction"),
]

df = pd.DataFrame(articles)
df.to_csv(RAW_CSV, index=False)
print(df.shape)
print(df[["article_id", "title", "publisher", "publication_date"]])
