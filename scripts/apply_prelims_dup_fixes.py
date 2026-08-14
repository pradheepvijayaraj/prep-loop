#!/usr/bin/env python3
"""Second-pass unique replacements for residual duplicate_stem inventory rows."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_DESKTOP = Path("/Users/pradheepvijayaraj/Desktop/LOOP DATA/PYQ/UPSC/CSE/PRELIMS/GS1")
_LOCAL = ROOT / "LOOP DATA/PYQ/UPSC/CSE/PRELIMS/GS1"
SRC = _DESKTOP if _DESKTOP.exists() else _LOCAL

REPLACEMENTS: dict[tuple[int, int], dict[str, Any]] = {}


def _r(year: int, num: int, question: str, options: list[str], correct: str) -> None:
    assert len(options) == 4
    REPLACEMENTS[(year, num)] = {
        "question": question.strip(),
        "options": [o.strip() for o in options],
        "correct": correct.upper(),
    }


# ── 2012 residual dups (higher slot numbers) ───────────────────────────────
_r(
    2012,
    52,
    """Which of the following statements is/are correct?

1. Viruses lack enzymes necessary for the generation of energy.
2. Viruses can be cultured in any synthetic medium.
3. Viruses are transmitted from one organism to another by biological vectors only.

Select the correct answer using the codes given below:""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)
_r(
    2012,
    58,
    """Consider the following statements:

The most effective contribution made by Dadabhai Naoroji to the cause of Indian National Movement was that he

1. exposed the economic exploitation of India by the British
2. interpreted the ancient Indian texts and restored the self-confidence of Indians
3. stressed the need for eradication of all the social evils before anything else

Which of the statements given above is/are correct?""",
    ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)
_r(
    2012,
    72,
    """Which of the following can be said to be essentially the parts of Inclusive Governance?

1. Permitting the Non-Banking Financial Companies to do banking
2. Establishing the Disputes Settlement Body of the WTO
3. Forming the National Investment Fund
4. National Rural Health Mission
5. National Mission on Agriculture Extension
6. Planning Commission’s plan for financial inclusion

Select the correct answer using the codes given below:""",
    ["1, 2 and 3 only", "4, 5 and 6 only", "1, 3 and 4 only", "1, 2, 3, 4, 5 and 6"],
    "B",
)
_r(
    2012,
    83,
    """In India, other than ensuring that public funds are used efficiently and for intended purpose, what is the importance of the office of the Comptroller and Auditor General (CAG)?

1. CAG exercises exchequer control on behalf of the Parliament when the President of India declares national emergency/financial emergency.
2. CAG reports on the execution of projects or programmes by the ministries are discussed by the Public Accounts Committee.
3. Information from CAG reports can be used by investigating agencies to press charges against those who have violated the law while managing public finances.
4. While dealing with the audit and accounting of government companies, CAG has certain judicial powers for prosecuting those who violate the law.

Which of the statements given above is/are correct?""",
    ["1, 3 and 4 only", "2 only", "2 and 3 only", "1, 2, 3 and 4"],
    "C",
)
_r(
    2012,
    93,
    """Consider the following statements:

Chlorofluorocarbons, known as ozone-depleting substances, are used

1. in the production of plastic foams
2. in the production of tubeless tyres
3. in cleaning certain electronic components
4. as pressurizing agents in aerosol cans

Which of the statements given above is/are correct?""",
    ["1, 2 and 3 only", "4 only", "1, 3 and 4 only", "1, 2, 3 and 4"],
    "C",
)
_r(
    2012,
    94,
    """What is the difference between the antelopes Oryx and Chiru?

(a) Oryx is adapted to live in hot and arid areas whereas Chiru is adapted to live in steppes and semi-desert areas of cold high mountains
(b) Oryx is poached for its antlers whereas Chiru is poached for its musk
(c) Oryx exists in western India only whereas Chiru exists in north-east India only
(d) None of the statements (a), (b) and (c) given above is correct""",
    [
        "Oryx is adapted to live in hot and arid areas whereas Chiru is adapted to live in steppes and semi-desert areas of cold high mountains",
        "Oryx is poached for its antlers whereas Chiru is poached for its musk",
        "Oryx exists in western India only whereas Chiru exists in north-east India only",
        "None of the statements (a), (b) and (c) given above is correct",
    ],
    "A",
)
# fix 94 as proper stem
_r(
    2012,
    94,
    """What is the difference between the antelopes Oryx and Chiru?""",
    [
        "Oryx is adapted to live in hot and arid areas whereas Chiru is adapted to live in steppes and semi-desert areas of cold high mountains",
        "Oryx is poached for its antlers whereas Chiru is poached for its musk",
        "Oryx exists in western India only whereas Chiru exists in north-east India only",
        "None of the statements (a), (b) and (c) given above is correct",
    ],
    "A",
)
_r(
    2012,
    96,
    """Which of the following is the chief characteristic of 'mixed farming'?""",
    [
        "Cultivation of both cash crops and food crops",
        "Cultivation of two or more crops in the same field",
        "Rearing of animals and cultivation of crops together",
        "None of the above",
    ],
    "C",
)
_r(
    2012,
    100,
    """A particular State in India has the following characteristics:

1. It is located on the same latitude which passes through northern Rajasthan.
2. It has over 80% of its area under forest cover.
3. Over 12% of forest cover constitutes Protected Area Network in this State.

Which one among the following States has all the above characteristics?""",
    ["Arunachal Pradesh", "Assam", "Himachal Pradesh", "Uttarakhand"],
    "A",
)

# ── 2014 ───────────────────────────────────────────────────────────────────
_r(
    2014,
    81,
    """Which of the following are some important pollutants released by steel industry in India?

1. Oxides of sulphur
2. Oxides of nitrogen
3. Carbon monoxide
4. Carbon dioxide

Select the correct answer using the code given below:""",
    ["1, 3 and 4 only", "2 and 3 only", "1 and 4 only", "1, 2, 3 and 4"],
    "D",
)

# ── 2016 residual dups ─────────────────────────────────────────────────────
_r(
    2016,
    31,
    """With reference to 'Pradhan Mantri Fasal Bima Yojana', consider the following statements:

1. Under this scheme, farmers will have to pay a uniform premium of two percent for any crop they cultivate in any season of the year.
2. This scheme covers post-harvest losses arising out of cyclones and unseasonal rains.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "B",
)
_r(
    2016,
    44,
    """In the cities of our country, which among the following atmospheric gases are normally considered in calculating the value of Air Quality Index?

1. Carbon dioxide
2. Carbon monoxide
3. Nitrogen dioxide
4. Sulfur dioxide
5. Methane

Select the correct answer using the code given below:""",
    ["1, 2 and 3 only", "2, 3 and 4 only", "1, 4 and 5 only", "1, 2, 3, 4 and 5"],
    "B",
)
_r(
    2016,
    70,
    """With reference to 'Astrosat', the astronomical observatory launched by India, which of the following statements is/are correct?

1. Other than USA and Russia, India is the only country to have launched a similar observatory into space.
2. Astrosat is a 2000 kg satellite, placed in an orbit at 1650 km above the surface of the Earth.

Select the correct answer using the code given below:""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "D",
)
_r(
    2016,
    100,
    """Consider the following statements:

1. The minimum age prescribed for any person to be a member of Panchayat is 25 years.
2. A Panchayat reconstituted after premature dissolution continues only for the remainder period.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "B",
)

# ── 2017 residual dups ─────────────────────────────────────────────────────
_r(
    2017,
    42,
    """What is the application of Somatic Cell Nuclear Transfer Technology?""",
    [
        "Production of biolarvicides",
        "Manufacture of biodegradable plastics",
        "Reproductive cloning of animals",
        "Production of organisms free of diseases",
    ],
    "C",
)
_r(
    2017,
    52,
    """The term 'Digital Single Market Strategy' seen in the news refers to""",
    [
        "ASEAN",
        "BRICS",
        "EU",
        "G20",
    ],
    "C",
)
_r(
    2017,
    55,
    """Consider the following statements:

1. National Payments Corporation of India (NPCI) helps in promoting the financial inclusion in the country.
2. NPCI has launched RuPay, a card payment scheme.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "C",
)
_r(
    2017,
    58,
    """Which of the following statements best describes the term 'Scheme for Sustainable Structuring of Stressed Assets (S4A)', recently seen in the news?""",
    [
        "It is a procedure for considering ecological costs of developmental schemes formulated by the Government.",
        "It is a scheme of RBI for reworking the financial structure of big corporate entities facing genuine difficulties.",
        "It is a disinvestment plan of the Government regarding Central Public Sector Undertakings.",
        "It is an important provision in The Insolvency and Bankruptcy Code recently implemented by the Government.",
    ],
    "B",
)
_r(
    2017,
    74,
    """Which one of the following statements is correct?""",
    [
        "In India, the same person cannot be appointed as Governor for two or more States at the same time.",
        "The Judges of the High Court of the States in India are appointed by the Governor of the State just as the Judges of the Supreme Court are appointed by the President.",
        "No procedure has been laid down in the Constitution of India for the removal of a Governor from his/her post.",
        "In the case of a Union Territory having a legislative setup, the Chief Minister is appointed by the Lt. Governor on the basis of majority support.",
    ],
    "C",
)
_r(
    2017,
    78,
    """Consider the following in respect of Indian Ocean Naval Symposium (IONS):

1. Inaugural IONS was held in India in 2015 under the chairmanship of the Indian Navy.
2. IONS is a voluntary initiative that seeks to increase maritime co-operation among navies of the littoral states of the Indian Ocean Region.

Which of the above statements is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "B",
)
_r(
    2017,
    96,
    """The Trade Disputes Act of 1929 provided for""",
    [
        "the participation of workers in the management of industries",
        "arbitrary powers to the management to quell industrial disputes",
        "an intervention by the British Court in the event of a trade dispute",
        "a system of tribunals and a ban on strikes",
    ],
    "D",
)
_r(
    2017,
    97,
    """Local self-government can be best explained as an exercise in""",
    [
        "Federalism",
        "Democratic decentralisation",
        "Administrative delegation",
        "Direct democracy",
    ],
    "B",
)
_r(
    2017,
    99,
    """Consider the following statements:

With reference to the Constitution of India, the Directive Principles of State Policy constitute limitations upon

1. legislative function
2. executive function

Which of the above statements is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "D",
)
_r(
    2017,
    100,
    """One of the implications of equality in society is the absence of""",
    [
        "Privileges",
        "Restraints",
        "Competition",
        "Ideology",
    ],
    "A",
)

# ── 2018 ───────────────────────────────────────────────────────────────────
_r(
    2018,
    63,
    """With reference to the provisions made under the National Food Security Act, 2013, consider the following statements:

1. The families coming under the category of 'below poverty line (BPL)' only are eligible to receive subsidised food grains.
2. The eldest woman in a household, of age 18 years or above, shall be the head of the household for the purpose of issuance of a ration card.
3. Pregnant women and lactating mothers are entitled to a 'take-home ration' of 1600 calories per day during pregnancy and for six months thereafter.

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "2 only", "1 and 3 only", "3 only"],
    "B",
)

# ── 2023 residual dups ─────────────────────────────────────────────────────
_r(
    2023,
    64,
    """Consider the following statements:

1. Jhelum River passes through Wular Lake.
2. Krishna River directly feeds Kolleru Lake.
3. Meandering of the Gandak River formed Kanwar Lake.

How many of the statements given above are correct?""",
    ["Only one", "Only two", "All three", "None"],
    "B",
)
_r(
    2023,
    73,
    """Consider the following statements:

1. Some microorganisms can grow in environments with temperature above the boiling point of water.
2. Some microorganisms can grow in environments with temperature below the freezing point of water.
3. Some microorganisms can grow in highly acidic environments with a pH below 3.

How many of the above statements are correct?""",
    ["Only one", "Only two", "All three", "None"],
    "C",
)
_r(
    2023,
    89,
    """Consider the following pairs:

Port : Well known as

1. Kamarajar Port : First major port in India registered as a company
2. Mundra Port : Largest privately owned port in India
3. Visakhapatnam Port : Largest container port in India

How many of the above pairs are correctly matched?""",
    ["Only one pair", "Only two pairs", "All three pairs", "None of the pairs"],
    "B",
)
_r(
    2023,
    95,
    """Which one of the following explains the practice of 'Vattakirutal' as mentioned in Sangam poems?""",
    [
        "Kings employing women bodyguards",
        "Learned persons assembling in royal courts to discuss religious and philosophical matters",
        "Young girls keeping watch over agricultural fields and driving away birds and animals",
        "A king defeated in a battle committing ritual suicide by starving himself to death",
    ],
    "D",
)
_r(
    2023,
    98,
    """Consider the following statements:

1. India accounts for 3.2% of global export of goods.
2. Many local companies in India use various preferential trade agreements for exporting their goods abroad.

Which of the statements given above is/are correct?""",
    ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    "B",
)

# ── 2026 ───────────────────────────────────────────────────────────────────
_r(
    2026,
    17,
    """With reference to the early Buddhist art, consider the following statements:

1. An empty seat was used to indicate the presence of the Buddha.
2. The Bodhi tree symbolized the enlightenment of the Buddha.
3. A stupa was used to symbolize the mahaparinirvana of the Buddha.

Which of the statements given above is/are correct?""",
    ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"],
    "A",
)


def apply_to_question(q: dict, rep: dict[str, Any]) -> None:
    q["question"] = rep["question"].rstrip()
    q["options"] = [
        {"id": chr(ord("A") + i), "text": t} for i, t in enumerate(rep["options"])
    ]
    q["answer"] = {"type": "single", "correct": [rep["correct"]]}
    q["content"] = [{"type": "paragraph", "text": q["question"]}]
    q["confidence"] = 0.99
    q["render_hint"] = "plain"


def main() -> int:
    dry = "--dry-run" in sys.argv
    total = 0
    by_year: dict[int, list] = {}
    for (y, n), rep in REPLACEMENTS.items():
        by_year.setdefault(y, []).append((n, rep))
    for y in sorted(by_year):
        path = SRC / str(y) / "paper.json"
        data = json.loads(path.read_text())
        by_num = {int(q.get("number") or 0): q for q in data["questions"]}
        print(f"Year {y}:")
        for n, rep in sorted(by_year[y]):
            q = by_num.get(n)
            if not q:
                print(f"  WARN missing Q{n}")
                continue
            apply_to_question(q, rep)
            total += 1
            print(f"  fixed Q{n}: {rep['question'][:65].replace(chr(10),' ')}...")
        if not dry:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"APPLIED={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
