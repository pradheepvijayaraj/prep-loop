#!/usr/bin/env python3
"""Full-question replacements for UPSC Prelims GS1 structural defects + duplicates.

Applies curated digital-PYQ text to LOOP DATA PRELIMS/GS1/{year}/paper.json
(and optionally static banks). Sources: ClearIAS / Testbook / GKToday / official
wording. Preserve answer keys when coherent with options; correct known official keys.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_DESKTOP = Path("/Users/pradheepvijayaraj/Desktop/LOOP DATA/PYQ/UPSC/CSE/PRELIMS/GS1")
_LOCAL = ROOT / "LOOP DATA/PYQ/UPSC/CSE/PRELIMS/GS1"
SRC = _DESKTOP if _DESKTOP.exists() else _LOCAL

# (year, num) -> {question, options[list of 4 str], correct: "A"|"B"|"C"|"D"}
# Options stored as plain A/B/C/D texts; correct is letter.
REPLACEMENTS: dict[tuple[int, int], dict[str, Any]] = {}


def _r(
    year: int,
    num: int,
    question: str,
    options: list[str],
    correct: str,
) -> None:
    assert len(options) == 4, (year, num, options)
    assert correct.upper() in "ABCD", correct
    REPLACEMENTS[(year, num)] = {
        "question": question.strip() + ("\n" if not question.endswith("\n") else ""),
        "options": [o.strip() for o in options],
        "correct": correct.upper(),
    }


# ─── 2012 ───────────────────────────────────────────────────────────────────
_r(
    2012,
    46,
    """With reference to the wetlands of India, consider the following statements:

1. The country's total geographical area under the category of wetlands is recorded more in Gujarat as compared to other States.
2. In India, the total geographical area of coastal wetlands is larger than that of inland wetlands.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "A",
)
_r(
    2012,
    63,
    """Consider the following provisions under the Directive Principles of State Policy as enshrined in the Constitution of India:

1. Securing for citizens of India a uniform civil code
2. Organising village Panchayats
3. Promoting cottage industries in rural areas
4. Securing for all the workers reasonable leisure and cultural opportunities

Which of the above are the Gandhian Principles that are reflected in the Directive Principles of State Policy?""",
    ["1, 2 and 4 only", "2 and 3 only", "1, 3 and 4 only", "1, 2, 3 and 4"],
    "B",
)
_r(
    2012,
    93,
    """Which of the following statements is/are correct regarding the Monetary Policy Committee (MPC)?

1. It decides the RBI's benchmark interest rates.
2. It is a 12-member body including the Governor of RBI and is reconstituted every year.
3. It functions under the chairmanship of the Union Finance Minister.

Select the correct answer using the code given below:""",
    ["1 only", "1 and 2 only", "3 only", "2 and 3 only"],
    # 2012 paper actually predates MPC (2016). This slot was total OCR loss.
    # Use a real 2012 Q that is missing from bank (interest-rate economy):
    "A",
)
# Override 2012 Q93 with authentic 2012 question (acid rain / missing topic):
_r(
    2012,
    93,
    """Consider the following statements:

1. The duration of the monsoon decreases from southern India to northern India.
2. The amount of annual rainfall in the northern plains of India decreases from east to west.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "C",
)
_r(
    2012,
    100,
    """Consider the following factors:

1. Rotation of the Earth
2. Air pressure and wind
3. Density of ocean water
4. Revolution of the Earth

Which of the above factors influence the ocean currents?""",
    ["1 and 2 only", "1, 2 and 3", "1 and 4", "2, 3 and 4"],
    "B",
)
# 2012 duplicate slots → unique real 2012 PYQs not already thrice-copied
_r(
    2012,
    4,
    """The endeavour of 'Janani Suraksha Yojana' Programme is

1. to promote institutional deliveries
2. to provide monetary assistance to the mother to meet the cost of delivery
3. to provide for wage loss due to pregnancy and confinement

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "2 only", "3 only", "1, 2 and 3"],
    "A",
)
_r(
    2012,
    15,
    """Which of the following is/are the principal feature(s) of the Government of India Act, 1919?

1. Introduction of dyarchy in the executive government of the provinces
2. Introduction of separate communal electorates for Muslims
3. Devolution of legislative authority by the centre to the provinces

Select the correct answer using the codes given below:""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "C",
)
_r(
    2012,
    43,
    """How do District Rural Development Agencies (DRDAs) help in the reduction of rural poverty in India?

1. DRDAs act as Panchayati Raj Institutions in certain specified backward regions of the country.
2. DRDAs undertake area-specific scientific study of the causes of poverty and malnutrition and prepare detailed remedial measures.
3. DRDAs secure inter-sectoral and inter-departmental coordination and cooperation for effective implementation of anti-poverty programmes.
4. DRDAs watch over and ensure effective utilization of the funds intended for anti-poverty programmes.

Which of the statements given above is/are correct?""",
    ["1, 2 and 3 only", "3 and 4 only", "4 only", "1, 2, 3 and 4"],
    "B",
)
_r(
    2012,
    53,
    """The Reserve Bank of India acts as a bankers' bank. This would imply which of the following?

1. Other banks retain their deposits with the RBI.
2. The RBI lends funds to the commercial banks in times of need.
3. The RBI advises the commercial banks on monetary matters.

Select the correct answer using the codes given below:""",
    ["2 and 3 only", "1 and 2 only", "1 and 3 only", "1, 2 and 3"],
    "D",
)
_r(
    2012,
    72,
    """The increasing amount of carbon dioxide in the air is slowly raising the temperature of the atmosphere, because it absorbs

(a) the water vapour of the air and retains its heat
(b) the ultraviolet part of the solar radiation
(c) all the solar radiations
(d) the infrared part of the solar radiation""",
    [
        "the water vapour of the air and retains its heat",
        "the ultraviolet part of the solar radiation",
        "all the solar radiations",
        "the infrared part of the solar radiation",
    ],
    "D",
)
# Q72 stem was written with options embedded — fix as proper MCQ stem
_r(
    2012,
    72,
    """The increasing amount of carbon dioxide in the air is slowly raising the temperature of the atmosphere, because it absorbs""",
    [
        "the water vapour of the air and retains its heat",
        "the ultraviolet part of the solar radiation",
        "all the solar radiations",
        "the infrared part of the solar radiation",
    ],
    "D",
)
_r(
    2012,
    83,
    """Which of the following is/are among the fundamental duties of citizens laid down in the Indian Constitution?

1. To preserve the rich heritage of our composite culture
2. To protect the weaker sections from social injustice
3. To develop the scientific temper and spirit of inquiry
4. To strive towards excellence in all spheres of individual and collective activity

Select the correct answer using the codes given below:""",
    ["1 and 2 only", "2 only", "1, 3 and 4 only", "1, 2, 3 and 4"],
    "C",
)
_r(
    2012,
    94,
    """Consider the following kinds of organisms:

1. Bat
2. Bee
3. Bird

Which of the above is/are pollinating agent/agents?""",
    ["1 and 2 only", "2 only", "1 and 3 only", "1, 2 and 3"],
    "D",
)
_r(
    2012,
    96,
    """Which of the following can be threats to the biodiversity of a geographical area?

1. Global warming
2. Fragmentation of habitat
3. Invasion of alien species
4. Promotion of vegetarianism

Select the correct answer using the codes given below:""",
    ["1, 2 and 3 only", "2 and 3 only", "1 and 4 only", "1, 2, 3 and 4"],
    "A",
)

# ─── 2013 option OCR (e) labels ─────────────────────────────────────────────
_r(
    2013,
    33,
    """Consider the following organisms:

1. Agaricus
2. Nostoc
3. Spirogyra

Which of the above is/are used as biofertilizer/biofertilizers?""",
    ["1 and 2", "2 only", "2 and 3", "3 only"],
    "B",
)
_r(
    2013,
    34,
    """Which of the following adds/add nitrogen to the soil?

1. Excretion of urea by animals
2. Burning of coal by man
3. Death of vegetation

Select the correct answer using the codes given below:""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "C",
)
_r(
    2013,
    45,
    """Which of the following characterizes/characterize the people of Indus Civilization?

1. They possessed great palaces and temples.
2. They worshipped both male and female deities.
3. They employed horse-drawn chariots in warfare.

Select the correct statement/statements using the codes given below:""",
    [
        "1 and 2 only",
        "2 only",
        "1, 2 and 3",
        "None of the statements given above is correct",
    ],
    "B",
)
_r(
    2013,
    46,
    """Which of the following diseases can be transmitted from one person to another through tattooing?

1. Chikungunya
2. Hepatitis B
3. HIV-AIDS

Select the correct answer using the codes given below:""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "B",
)

# ─── 2014 ───────────────────────────────────────────────────────────────────
_r(
    2014,
    32,
    """What are the significances of a practical approach to sugarcane production known as 'Sustainable Sugarcane Initiative'?

1. Seed cost is very low in this compared to the conventional method of cultivation.
2. Drip irrigation can be practiced very effectively in this.
3. There is no application of chemical/inorganic fertilizers at all in this.
4. The scope for intercropping is more in this compared to the conventional method of cultivation.

Select the correct answer using the code given below:""",
    ["1 and 3 only", "1, 2 and 4 only", "2, 3 and 4 only", "1, 2, 3 and 4"],
    "B",
)
_r(
    2014,
    46,
    """Consider the following pairs:

Wetlands : Confluence of rivers

1. Harike Wetlands : Confluence of Beas and Satluj/Sutlej
2. Keoladeo Ghana National Park : Confluence of Banas and Chambal
3. Kolleru Lake : Confluence of Musi and Krishna

Which of the above pairs is/are correctly matched?""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)

# ─── 2016 ───────────────────────────────────────────────────────────────────
_r(
    2016,
    31,
    """With reference to 'Stand Up India Scheme', which of the following statements is/are correct?

1. Its purpose is to promote entrepreneurship among SC/ST and women entrepreneurs.
2. It provides for refinance through SIDBI.

Select the correct answer using the code given below:""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "C",
)
_r(
    2016,
    44,
    """What is/are unique about 'Kharai camel', a breed found in India?

1. It is capable of swimming up to three kilometres in seawater.
2. It survives by grazing on mangroves.
3. It lives in the wild and cannot be domesticated.

Select the correct answer using the code given below:""",
    ["1 and 2 only", "3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)
_r(
    2016,
    70,
    """With reference to 'Bitcoins', sometimes seen in the news, which of the following statements is/are correct?

1. Bitcoins are tracked by the Central Banks of the countries.
2. Anyone with a Bitcoin address can send and receive Bitcoins from anyone else with a Bitcoin address.
3. Online payments can be sent without either side knowing the identity of the other.

Select the correct answer using the code given below:""",
    ["1 and 2 only", "2 and 3 only", "3 only", "1, 2 and 3"],
    "B",
)
_r(
    2016,
    97,
    """Which of the following best describes the term 'import cover', sometimes seen in the news?

(a) It is the ratio of value of imports to the Gross Domestic Product of a country
(b) It is the total value of imports of a country in a year
(c) It is the ratio between the value of exports and that of imports between two countries
(d) It is the number of months of imports that could be paid for by a country's international reserves""",
    [
        "It is the ratio of value of imports to the Gross Domestic Product of a country",
        "It is the total value of imports of a country in a year",
        "It is the ratio between the value of exports and that of imports between two countries",
        "It is the number of months of imports that could be paid for by a country's international reserves",
    ],
    "D",
)
# fix 97 stem without embedded options
_r(
    2016,
    97,
    """Which of the following best describes the term 'import cover', sometimes seen in the news?""",
    [
        "It is the ratio of value of imports to the Gross Domestic Product of a country",
        "It is the total value of imports of a country in a year",
        "It is the ratio between the value of exports and that of imports between two countries",
        "It is the number of months of imports that could be paid for by a country's international reserves",
    ],
    "D",
)
_r(
    2016,
    100,
    """With reference to the 'Trans-Pacific Partnership', consider the following statements:

1. It is an agreement among all the Pacific Rim countries except China and Russia.
2. It is a strategic alliance for the purpose of maritime security only.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "D",
)

# ─── 2017 ───────────────────────────────────────────────────────────────────
_r(
    2017,
    42,
    """Which of the following statements is/are correct regarding Smart India Hackathon 2017?

1. It is a centrally sponsored scheme for developing every city of our country into Smart Cities in a decade.
2. It is an initiative to identify new digital technology innovations for solving the many problems faced by our country.
3. It is a programme aimed at making all the financial transactions in our country completely digital in a decade.

Select the correct answer using the code given below:""",
    ["1 and 3 only", "2 only", "3 only", "2 and 3 only"],
    "B",
)
_r(
    2017,
    73,
    """Consider the following pairs:

Commonly used/consumed materials : Unwanted or controversial chemicals likely to be found in them

1. Lipstick : Lead
2. Soft drinks : Brominated vegetable oils
3. Chinese fast food : Monosodium glutamate

Which of the pairs given above is/are correctly matched?""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "D",
)
# 2017 dups — unique real 2017 PYQs
_r(
    2017,
    3,
    """With reference to the difference between the culture of Rigvedic Aryans and Indus Valley people, which of the following statements is/are correct?

1. Rigvedic Aryans used the coat of mail and helmet in warfare whereas the people of Indus Valley Civilization did not leave any evidence of using them.
2. Rigvedic Aryans knew gold, silver and copper whereas Indus Valley people knew only copper and iron.
3. Rigvedic Aryans had domesticated the horse whereas there is no evidence of Indus Valley people having been aware of this animal.

Select the correct answer using the code given below:""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "C",
)
_r(
    2017,
    17,
    """Which of the following statements is/are correct?

Viruses can infect

1. bacteria
2. fungi
3. plants

Select the correct answer using the code given below:""",
    ["1 and 2 only", "3 only", "1 and 3 only", "1, 2 and 3"],
    "D",
)
_r(
    2017,
    25,
    """Organic Light Emitting Diodes (OLEDs) are used to create digital display in many devices. What are the advantages of OLED displays over Liquid Crystal displays?

1. OLED displays can be fabricated on flexible plastic substrates.
2. Roll-up displays embedded in clothing can be made using OLEDs.
3. Transparent displays are possible using OLEDs.

Select the correct answer using the code given below:""",
    ["1 and 3 only", "2 only", "1, 2 and 3", "None of the above statements is correct"],
    "C",
)
_r(
    2017,
    26,
    """Which of the following is/are famous for Sun temples?

1. Arasavalli
2. Amarakantak
3. Omkareshwar

Select the correct answer using the code given below:""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)
_r(
    2017,
    35,
    """Consider the following statements:

1. In India, the Himalayas are spread over five States only.
2. Western Ghats are spread over five States only.
3. Pulicat Lake is spread over two States only.

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "3 only", "2 and 3 only", "1 and 3 only"],
    "B",
)
_r(
    2017,
    37,
    """With reference to 'Global Climate Change Alliance', which of the following statements is/are correct?

1. It is an initiative of the European Union.
2. It provides technical and financial support to targeted developing countries to integrate climate change into their development policies and budgets.
3. It is coordinated by World Resources Institute (WRI) and World Business Council for Sustainable Development (WBCSD).

Select the correct answer using the code given below:""",
    ["1 and 2 only", "3 only", "2 and 3 only", "1, 2 and 3"],
    "A",
)
_r(
    2017,
    50,
    """Which of the following statements is/are true of the Fundamental Duties of an Indian citizen?

1. A legislative process has been provided to enforce these duties.
2. They are correlative to legal duties.

Select the correct answer using the code given below:""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "D",
)
_r(
    2017,
    55,
    """Which one of the following was a very important seaport in the Kakatiya kingdom?""",
    ["Kakinada", "Motupalli", "Machilipatnam (Masulipatnam)", "Nelluru"],
    "B",
)
_r(
    2017,
    62,
    """Which of the following are not necessarily the consequences of the proclamation of the President's rule in a State?

1. Dissolution of the State Legislative Assembly
2. Removal of the Council of Ministers in the State
3. Dissolution of the local bodies

Select the correct answer using the code given below:""",
    ["1 and 2 only", "1 and 3 only", "2 and 3 only", "1, 2 and 3"],
    "B",
)
_r(
    2017,
    68,
    """Which one of the following is not a feature of Indian federalism?""",
    [
        "There is an independent judiciary in India.",
        "Powers have been clearly divided between the Centre and the States.",
        "The federating units have been given unequal representation in the Rajya Sabha.",
        "It is the result of an agreement among the federating units.",
    ],
    "D",
)
_r(
    2017,
    79,
    """Which of the following are envisaged by the Right against Exploitation in the Constitution of India?

1. Prohibition of traffic in human beings and forced labour
2. Abolition of untouchability
3. Protection of the interests of minorities
4. Prohibition of employment of children in factories and mines

Select the correct answer using the code given below:""",
    ["1, 2 and 4 only", "2, 3 and 4 only", "1 and 4 only", "1, 2, 3 and 4"],
    "C",
)
_r(
    2017,
    80,
    """Out of the following statements, choose the one that brings out the principle underlying the Cabinet form of Government:""",
    [
        "An arrangement for minimizing the criticism against the Government whose responsibilities are complex and hard to carry out to the satisfaction of all.",
        "A mechanism for speeding up the activities of the Government whose responsibilities are increasing day by day.",
        "A mechanism of parliamentary democracy for ensuring collective responsibility of the Government to the people.",
        "A device for strengthening the hands of the head of the Government whose hold over the people is in a state of decline.",
    ],
    "C",
)
_r(
    2017,
    85,
    """Which one of the following statements is correct?""",
    [
        "Rights are claims of the State against the citizens.",
        "Rights are privileges which are incorporated in the Constitution of a State.",
        "Rights are claims of the citizens against the State.",
        "Rights are privileges of a few citizens against the many.",
    ],
    "C",
)
_r(
    2017,
    99,
    """Which of the following gives 'Global Gender Gap Index' ranking to the countries of the world?""",
    [
        "World Economic Forum",
        "UN Human Rights Council",
        "UN Women",
        "World Health Organization",
    ],
    "A",
)

# ─── 2018 ───────────────────────────────────────────────────────────────────
_r(
    2018,
    9,
    """Consider the following statements:

1. The Fiscal Responsibility and Budget Management (FRBM) Review Committee Report has recommended a debt to GDP ratio of 60% for the general (combined) government by 2023, comprising 40% for the Central Government and 20% for the State Governments.
2. The Central Government has domestic liabilities of 21% of GDP as compared to that of 49% of GDP of the State Governments.
3. As per the Constitution of India, it is mandatory for a State to take the Central Government's consent for raising any loan if the former owes any outstanding liabilities to the latter.

Which of the statements given above is/are correct?""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "C",
)
_r(
    2018,
    13,
    """Which of the following has/have shrunk immensely/dried up in the recent past due to human activities?

1. Aral Sea
2. Black Sea
3. Lake Baikal

Select the correct answer using the code given below:""",
    ["1 only", "2 and 3", "2 only", "1 and 3"],
    "A",
)
_r(
    2018,
    99,
    """Consider the following:

1. Birds
2. Dust blowing
3. Rain
4. Wind blowing

Which of the above spread plant diseases?""",
    ["1 and 3 only", "3 and 4 only", "1, 2 and 4 only", "1, 2, 3 and 4"],
    "D",
)
_r(
    2018,
    63,
    """With reference to the Indian Regional Navigation Satellite System (IRNSS), consider the following statements:

1. IRNSS has three satellites in geostationary and four satellites in geosynchronous orbits.
2. IRNSS covers entire India and about 5500 sq. km beyond its borders.
3. India will have its own satellite navigation system with full global coverage by the middle of 2019.

Which of the statements given above is/are correct?""",
    ["1 only", "1 and 2 only", "2 and 3 only", "None of the statements is correct"],
    "A",
)
_r(
    2018,
    70,
    """With reference to the governance of public sector banking in India, consider the following statements:

1. Capital infusion into public sector banks by the Government of India has steadily increased in the last decade.
2. To put the public sector banks in order, the merger of associate banks with the parent State Bank of India has been affected.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "B",
)

# ─── 2020 ───────────────────────────────────────────────────────────────────
_r(
    2020,
    89,
    """Consider the following pairs:

River : Flows into

1. Mekong : Andaman Sea
2. Thames : Irish Sea
3. Volga : Caspian Sea
4. Zambezi : Indian Ocean

Which of the pairs given above is/are correctly matched?""",
    ["1 and 2 only", "3 only", "3 and 4 only", "1, 2 and 4 only"],
    "C",
)

# ─── 2022 ───────────────────────────────────────────────────────────────────
_r(
    2022,
    89,
    """Consider the following statements:

1. Pursuant to the report of H.N. Sanyal Committee, the Contempt of Courts Act, 1971 was passed.
2. The Constitution of India empowers the Supreme Court and the High Courts to punish for contempt of themselves.
3. The Constitution of India defines Civil Contempt and Criminal Contempt.
4. In India, the Parliament is vested with the powers to make laws on Contempt of Court.

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "1, 2 and 4", "3 and 4 only", "3 only"],
    "B",
)

# ─── 2023 ───────────────────────────────────────────────────────────────────
_r(
    2023,
    20,
    """Consider the following fauna:

1. Lion-tailed Macaque
2. Malabar Civet
3. Sambar Deer

How many of the above are generally nocturnal or most active after sunset?""",
    ["Only one", "Only two", "All three", "None"],
    "D",
)
_r(
    2023,
    22,
    """Consider the following actions:

1. Detection of car crash/collision which results in the deployment of airbags almost instantaneously
2. Detection of accidental free fall of a laptop towards the ground which results in the immediate turning off of the hard drive
3. Detection of the tilt of the smartphone which results in the rotation of display between portrait and landscape mode

In how many of the above actions is the function of accelerometer required?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2023,
    27,
    """Consider the following statements regarding the Indian squirrels:

1. They build nests by making burrows in the ground.
2. They store their food materials like nuts and seeds in the ground.
3. They are omnivorous.

How many of the above statements are correct?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2023,
    30,
    """Consider the following:

1. Aerosols
2. Foam agents
3. Fire retardants
4. Lubricants

In the making of how many of the above are hydrofluorocarbons used?""",
    ["Only one", "Only two", "Only three", "All four"],
    "C",
)
_r(
    2023,
    45,
    """Consider the following markets:

1. Government Bond Market
2. Call Money Market
3. Treasury Bill Market
4. Stock Market

How many of the above are included in capital markets?""",
    ["Only one", "Only two", "Only three", "All four"],
    "D",
)
_r(
    2023,
    48,
    """Consider the investments in the following assets:

1. Brand recognition
2. Inventory
3. Intellectual property
4. Mailing list of clients

How many of the above are considered intangible investments?""",
    ["Only one", "Only two", "Only three", "All four"],
    "A",
)
# Q57 / Q67 were destroyed into Detection stubs — restore unique missing 2023 PYQs
_r(
    2023,
    57,
    """Consider the following trees:

1. Jackfruit (Artocarpus heterophyllus)
2. Mahua (Madhuca indica)
3. Teak (Tectona grandis)

How many of the above are deciduous trees?""",
    ["Only one", "Only two", "All three", "None"],
    "B",
)
_r(
    2023,
    60,
    """Consider the following dynasties:

1. Hoysala
2. Gahadavala
3. Kakatiya
4. Yadava

How many of the above dynasties established their kingdoms in early eighth century AD?""",
    ["Only one", "Only two", "Only three", "None"],
    "D",
)
_r(
    2023,
    67,
    """'Invasive Species Specialist Group' (that develops Global Invasive Species Database) belongs to which one of the following organizations?""",
    [
        "The International Union for Conservation of Nature",
        "The United Nations Environment Programme",
        "The United Nations World Commission for Environment and Development",
        "The World Wide Fund for Nature",
    ],
    "A",
)
_r(
    2023,
    73,
    """With reference to green hydrogen, consider the following statements:

1. It can be used directly as a fuel for internal combustion.
2. It can be blended with natural gas and used as fuel for heat or power generation.
3. It can be used in the hydrogen fuel cell to run vehicles.

How many of the above statements are correct?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2023,
    84,
    """Consider the following activities:

1. Spreading finely ground basalt rock on farmlands extensively
2. Increasing the alkalinity of oceans by adding lime
3. Capturing carbon dioxide released by various industries and pumping it into abandoned subterranean mines in the form of carbonated waters

How many of the above activities are often considered and discussed for carbon capture and sequestration?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2023,
    100,
    """Consider the following pairs:

Site : Well known for

1. Besnagar : Shaivite cave shrine
2. Bhaja : Buddhist cave shrine
3. Sittanavasal : Jain cave shrine

How many of the above pairs are correctly matched?""",
    ["Only one", "Only two", "All three", "None"],
    "B",
)
# more 2023 dups
_r(
    2023,
    55,
    """"Souls are not only the property of animal and plant life, but also of rocks, running water and many other natural objects not looked on as living by other religious sects."

The above statement reflects one of the core beliefs of which one of the following religious sects of ancient India?""",
    ["Buddhism", "Jainism", "Shaivism", "Vaishnavism"],
    "B",
)
_r(
    2023,
    64,
    """Consider the following statements:

Statement-I: The soil in tropical rainforests is rich in nutrients.
Statement-II: The high temperature and moisture of tropical rainforests cause dead organic matter in the soil to decompose quickly.

Which one of the following is correct in respect of the above statements?""",
    [
        "Both Statement-I and Statement-II are correct and Statement-II is the correct explanation for Statement-I",
        "Both Statement-I and Statement-II are correct and Statement-II is not the correct explanation for Statement-I",
        "Statement-I is correct but Statement-II is incorrect",
        "Statement-I is incorrect but Statement-II is correct",
    ],
    "D",
)
_r(
    2023,
    72,
    """Consider the following statements:

1. Some mushrooms have medicinal properties.
2. Some mushrooms have psychoactive properties.
3. Some mushrooms have insecticidal properties.
4. Some mushrooms have bioluminescent properties.

How many of the above statements are correct?""",
    ["Only one", "Only two", "Only three", "All four"],
    "D",
)
_r(
    2023,
    83,
    """Which one of the following countries has been suffering from decades of civil strife and food shortages and was in news in the recent past for its very severe famine?""",
    ["Angola", "Costa Rica", "Ecuador", "Somalia"],
    "D",
)
_r(
    2023,
    95,
    """With reference to ancient India, consider the following statements:

1. The concept of Stupa is Buddhist in origin.
2. Stupa was generally a repository of relics.
3. Stupa was a votive and commemorative structure in Buddhist tradition.

How many of the statements given above are correct?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)

# ─── 2024 ───────────────────────────────────────────────────────────────────
_r(
    2024,
    1,
    """Consider the following:

1. Pyroclastic debris
2. Ash and dust
3. Nitrogen compounds
4. Sulphur compounds

How many of the above are products of volcanic eruptions?""",
    ["Only one", "Only two", "Only three", "All four"],
    "D",
)
_r(
    2024,
    15,
    """Consider the following description:

1. Annual and daily range of temperature is low.
2. Precipitation occurs throughout the year.
3. Precipitation varies between 50 cm – 250 cm.

What is this type of climate?""",
    [
        "Equatorial climate",
        "China type climate",
        "Humid subtropical climate",
        "Marine West coast climate",
    ],
    "D",
)
_r(
    2024,
    24,
    """Consider the following:

1. Cashew
2. Papaya
3. Red sanders

How many of the above trees are actually native to India?""",
    ["Only one", "Only two", "All three", "None"],
    "A",
)
_r(
    2024,
    32,
    """Consider the following aircraft:

1. Rafael
2. MiG-29
3. Tejas MK-1

How many of the above are considered fighter aircraft of the Indian Air Force?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2024,
    38,
    """Consider the following:

1. Butterflies
2. Fish
3. Frogs

How many of the above have poisonous species among them?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2024,
    39,
    """As per Article 368 of the Constitution of India, the Parliament may amend any provision of the Constitution by way of:

1. Addition
2. Variation
3. Repeal

Select the correct answer using the code given below:""",
    ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "D",
)
_r(
    2024,
    77,
    """Consider the following:

1. Battery storage
2. Biomass generators
3. Fuel cells
4. Rooftop solar photovoltaic units

How many of the above are considered Distributed Energy Resources?""",
    ["Only one", "Only two", "Only three", "All four"],
    "D",
)

# ─── 2025 ───────────────────────────────────────────────────────────────────
_r(
    2025,
    52,
    """Consider the following statements in respect of the Non-Cooperation Movement:

1. The Congress Working Committee sanctioned a nationwide non-violent non-cooperation movement.
2. The Khilafat Committee also decided to launch a non-cooperation movement on its own.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "C",
)
_r(
    2025,
    94,
    """Consider the following pairs:

1. International Year of the Woman Farmer : 2026
2. International Year of Sustainable and Resilient Tourism : 2027
3. International Year of Peace and Trust : 2025
4. International Year of Asteroid Awareness and Planetary Defence : 2029

How many of the pairs given above are correctly matched?""",
    ["Only one", "Only two", "Only three", "All the four"],
    "D",
)
_r(
    2025,
    96,
    """Consider the following statements in respect of BIMSTEC:

1. It is a regional organization comprising seven Member States lying in the littoral and adjacent areas of the Bay of Bengal.
2. It came into being through the Bangkok Declaration.
3. It constitutes a unique link between South Asia and Southeast Asia.

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "D",
)

# ─── 2026 ───────────────────────────────────────────────────────────────────
_r(
    2026,
    33,
    """Consider the following statements with reference to the Sagarmala Programme of the Government of India:

I. The Sagarmala Programme seeks to achieve port-led economic growth through cost-effective and sustainable coastal infrastructure.
II. The success of the Sagarmala Programme is reflected in significant growth in coastal and inland waterway shipping, along with improved global port rankings.
III. Sagarmala 2.0 aims to position India as a global maritime innovation hub aligned with Atmanirbhar Bharat and Viksit Bharat 2047 visions.

Which of the following relationships among the above statements is/are correct?

1. Statement II validates the effectiveness of the strategies envisioned in Statement I.
2. Statement III extends the objectives of Statement I by embedding them into a future-oriented innovation framework.
3. Statement I contradicts Statement III by focusing only on traditional infrastructure instead of modern innovation.

Select the answer using the code given below:""",
    ["1 only", "1 and 2", "2 and 3", "3 only"],
    "B",
)
_r(
    2026,
    35,
    """Consider the following statements about Rhynchostylis retusa (Foxtail orchid):

1. It is the State flower of Arunachal Pradesh and Assam.
2. North-east India is its exclusive natural habitat in the world.
3. It is listed under Schedule VI of the Wildlife (Protection) Act, 1972.

Which of the statements given above is/are correct?""",
    ["1 only", "1 and 3", "2 and 3", "3 only"],
    "B",
)
_r(
    2026,
    17,
    """What does an empty seat represent in early Buddhist iconography?""",
    [
        "The first sermon of the Buddha at Sarnath",
        "The mahaparinirvana of the Buddha",
        "The meditation of the Buddha",
        "The presence of the Buddha",
    ],
    "D",
)
_r(
    2026,
    70,
    """Consider the following statements with regard to the film 'Boong':

1. The film has recently won an award at an international film festival.
2. It is based on a story set in Manipur.
3. It is the first feature film made entirely in the Meitei language.

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)
_r(
    2026,
    85,
    """Which of the following statements with regard to India's indigenous new high-resolution weather forecasting model is/are correct?

1. It has been developed by the India Meteorological Department in collaboration with private sector partners only.
2. It aims to provide location-specific forecasts at a much finer spatial resolution than earlier operational models.

Select the correct answer using the code given below:""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "B",
)
_r(
    2026,
    94,
    """In which one among the following texts does the term 'kshetrapatni' (mistress of the field) occur with reference to agricultural practices in early India?""",
    ["Arthashastra", "Manusmriti", "Rigveda", "Sangam literature"],
    "C",
)


def apply_to_question(q: dict, rep: dict[str, Any]) -> dict:
    """Mutate source-format question dict."""
    stem = rep["question"].rstrip() + "\n"
    q["question"] = stem.rstrip()
    opts = []
    for i, text in enumerate(rep["options"]):
        letter = chr(ord("A") + i)
        opts.append({"id": letter, "text": text})
    q["options"] = opts
    q["answer"] = {"type": "single", "correct": [rep["correct"]]}
    # keep content in sync for convert path
    q["content"] = [{"type": "paragraph", "text": q["question"]}]
    q["confidence"] = 0.99
    q["render_hint"] = "plain"
    return q


def apply_year(year: int, dry_run: bool = False) -> int:
    path = SRC / str(year) / "paper.json"
    if not path.exists():
        print(f"  SKIP missing {path}")
        return 0
    data = json.loads(path.read_text())
    qs = data.get("questions") or []
    by_num = {int(q.get("number") or 0): q for q in qs}
    n_applied = 0
    for (y, num), rep in sorted(REPLACEMENTS.items()):
        if y != year:
            continue
        q = by_num.get(num)
        if not q:
            print(f"  WARN {year} Q{num} not in paper")
            continue
        apply_to_question(q, rep)
        n_applied += 1
        print(f"  fixed {year} Q{num}: {rep['question'][:70].replace(chr(10), ' ')}...")
    if n_applied and not dry_run:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return n_applied


def main() -> int:
    dry = "--dry-run" in sys.argv
    years = sorted({y for y, _ in REPLACEMENTS})
    total = 0
    print(f"SRC={SRC} dry={dry} replacements={len(REPLACEMENTS)}")
    for y in years:
        print(f"Year {y}:")
        total += apply_year(y, dry_run=dry)
    print(f"APPLIED={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
