#!/usr/bin/env python3
"""Unit tests for prelims scar scan + repair helpers (shipped code path)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prelims_quality import (  # noqa: E402
    already_numbered_list,
    count_numbered_statements,
    fix_select_glued,
    high_severity_scars,
    repair_stem,
    scan_all_static,
)

FIX = ROOT / "scripts" / "fixtures" / "prelims_scars"


def test_vitasta_scar_detected_and_repaired():
    scarred = (FIX / "vitasta_scarred.txt").read_text()
    opts = [
        {"text": "1 and 2"},
        {"text": "3 and 4"},
        {"text": "3 only"},
        {"text": "4 only"},
    ]
    scars = high_severity_scars(scarred, opts)
    assert scars, "scarred vitasta must flag high-severity"
    repaired, tags = repair_stem(scarred, opts)
    assert count_numbered_statements(repaired) >= 4
    assert "1. Vitasta : Chenab" in repaired
    assert "2. Asikni : Jhelum" in repaired
    assert "3. Parushni : Ravi" in repaired
    assert "4. Yavyavati : Beas" in repaired
    assert "5. Select" not in repaired
    assert not high_severity_scars(repaired, opts), high_severity_scars(repaired, opts)


def test_eu_unnumbered_repaired():
    scarred = (FIX / "eu_scarred.txt").read_text()
    opts = [{"text": "1 and 2"}, {"text": "3 and 4"}, {"text": "2 and 3"}, {"text": "1 only"}]
    assert "code_opts_no_statements" in high_severity_scars(scarred, opts)
    repaired, tags = repair_stem(scarred, opts)
    assert count_numbered_statements(repaired) >= 4
    assert "1. Belarus" in repaired
    assert "4. Switzerland" in repaired
    assert not high_severity_scars(repaired, opts), high_severity_scars(repaired, opts)


def test_inline_numbered_to_multiline():
    scarred = (FIX / "inline_scarred.txt").read_text()
    opts = [
        {"text": "1 and 2 only"},
        {"text": "2 and 3 only"},
        {"text": "1 and 3 only"},
        {"text": "1, 2 and 3"},
    ]
    repaired, _ = repair_stem(scarred, opts)
    assert count_numbered_statements(repaired) >= 3


def test_already_numbered_not_destroyed():
    clean = (FIX / "vitasta_clean.txt").read_text()
    opts = [{"text": "3 only"}]
    repaired, tags = repair_stem(clean, opts)
    assert "1. Vitasta : Chenab" in repaired
    assert count_numbered_statements(repaired) >= 4
    import re

    assert not re.search(r"(?m)^\s*\d+[\.)]\s*Select the", repaired, re.I)


def test_select_glued_fix():
    s = "1. foo\n2. bar Select the answer using the code given below"
    fixed = fix_select_glued(s)
    assert "Select the answer" in fixed
    assert "\n\nSelect" in fixed or fixed.count("Select") == 1


def test_count_numbered():
    assert count_numbered_statements("1. a\n2. b\n3. c") >= 3
    assert already_numbered_list("1. a\n2. b")


def test_static_prelims_zero_high_severity_scars():
    root = ROOT / "static" / "upsc" / "prelims-gs1"
    assert root.is_dir(), root
    results = scan_all_static(root)
    total = sum(len(v) for v in results.values())
    assert total == 0, {y: hits for y, hits in results.items() if hits}


def test_convert_preserves_numbered_vitasta_stem():
    conv_path = ROOT / "scripts" / "convert_upsc_to_banks.py"
    spec = importlib.util.spec_from_file_location("convert_upsc_to_banks", conv_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    clean = (FIX / "vitasta_clean.txt").read_text().strip()
    q = {
        "question": clean,
        "content": [{"type": "paragraph", "text": clean}],
        "options": [
            {"id": "A", "text": "1 and 2"},
            {"id": "B", "text": "3 and 4"},
            {"id": "C", "text": "3 only"},
            {"id": "D", "text": "4 only"},
        ],
        "answer": {"type": "single", "correct": ["C"]},
    }
    stem = mod.build_stem(q)
    assert "1. Vitasta : Chenab" in stem
    assert "5. Select" not in stem
    out = mod.convert_question(q, "upsc_2026_gs1", mod.PAPER_META[("PRELIMS", "GS1")], 3)
    assert out and "1. Vitasta : Chenab" in out[0]["question"]
    assert out[0]["correctAnswers"] == ["c"]




def test_detects_two_topic_interleave():
    scarred = (FIX / "interleave_rbi_scarred.txt").read_text()
    scars = high_severity_scars(scarred, [{"text": "1 only"}, {"text": "2 only"}, {"text": "Both 1 and 2"}, {"text": "Neither 1 nor 2"}])
    assert "two_topic_interleave" in scars or "severe_ocr_typo" in scars, scars


def test_detects_word_split_airport_list():
    scarred = (FIX / "airport_wordsplit_scarred.txt").read_text()
    opts = [{"text": "1 and 2 only"}, {"text": "2 and 3 only"}, {"text": "1 and 3 only"}, {"text": "1, 2 and 3"}]
    scars = high_severity_scars(scarred, opts)
    assert "word_split_list" in scars, scars


def test_detects_web_chrome_option():
    chrome = (FIX / "forumias_chrome_option.txt").read_text()
    opts = [{"text": "Only one"}, {"text": "Only two"}, {"text": "Only three"}, {"text": chrome}]
    stem = "How many of the above statements are correct?"
    scars = high_severity_scars(stem, opts)
    assert "web_chrome_pollution" in scars or "option_overlong_chrome" in scars, scars


def test_skeptic_flagged_static_qs_clean():
    """Skeptic-flagged questions must be coherent (structural + no chrome)."""
    checks = [
        (2012, 75, "money supply"),
        (2012, 77, "bankers"),
        (2012, 93, "chlorofluorocarbon"),
        (2014, 16, "Business Correspondent"),
        (2016, 29, "Core Banking"),
        (2016, 66, "Bitcoin"),
        (2016, 100, "minimum age prescribed for any person"),
        (2023, 22, "accelerometer"),
        (2023, 41, "President of India"),
        (2024, 1, "Pyroclastic"),
        (2024, 12, "Donyi Polo Airport"),
        (2024, 24, "Cashew"),
    ]
    from prelims_mcq_complete import validate_mcq

    for year, num, must_in_stem in checks:
        data = json.loads((ROOT / "static/upsc/prelims-gs1" / f"{year}.json").read_text())
        q = data["questions"][num - 1]
        assert must_in_stem.lower() in q["question"].lower(), (year, num, q["question"][:120])
        scars = high_severity_scars(q["question"], q["options"])
        assert not scars, (year, num, scars, q["question"][:100], q["options"])
        reasons = validate_mcq(q["question"], q["options"])
        assert not reasons, (year, num, reasons, q["question"][:100])
        # no chrome in options
        for o in q["options"]:
            assert "ForumIAS" not in (o.get("text") or "")
            assert "Share this" not in (o.get("text") or "")
            assert len(o.get("text") or "") < 300
        # answer present
        assert q.get("correctAnswers")




def test_detects_false_number_and_fragments():
    stem = "The Committee consists of not more than\n25. Members of the Lok Sabha"
    assert "false_number_list_break" in high_severity_scars(stem, [{"text":"1 only"}])
    stem2 = "Consider the following pairs : Terms\n1. Terms\n2. Context\n3. Topic Belle II"
    assert "pair_table_header_as_items" in high_severity_scars(stem2, [{"text":"2 only"}])
    opts = [{"text":"1 and 83 only"},{"text":"2 only"},{"text":"2 and 3 only"},{"text":"1, 2 and 3 CYRF-F-TXLI (2"}]
    assert "exam_booklet_code_option" in high_severity_scars("pairs", opts)


def test_skeptic_round3_static_clean():
    checks = [
        (2018, 70, "Hind Mazdoor Sabha"),  # Source-verified replacement for a duplicate stem
        (2014, 97, "Vitamin C"),
        (2023, 69, "Stability and Growth Pact"),
        (2013, 51, "Public Accounts"),
        (2025, 39, "Botswana"),
        (2019, 53, "18 States"),
        (2024, 86, "Arctic Circle"),
        (2012, 2, "Article 21"),
        (2012, 20, "Kuchipudi"),
    ]
    for year, num, key in checks:
        data = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())
        q = data["questions"][num - 1]
        assert key.lower() in q["question"].lower(), (year, num, q["question"][:80])
        scars = high_severity_scars(q["question"], q["options"])
        assert not scars, (year, num, scars)
        for o in q["options"]:
            assert "CYRF" not in (o.get("text") or "")
            t = (o.get("text") or "").lower()
            # bare OCR booklet labels like "(e) 2 and 3" must not appear
            assert not (t.startswith("(e)") or t.startswith("(bj)"))


def test_static_prelims_inventory_empty():
    """Primary gate: every prelims GS1 MCQ must pass structural validate_mcq."""
    from prelims_mcq_complete import inventory_prelims

    inv = inventory_prelims(ROOT / "static" / "upsc" / "prelims-gs1")
    assert inv == [], inv[:15]


def test_validate_mcq_catches_real_garbage():
    from prelims_mcq_complete import validate_mcq

    bad = "Consider the following statements:\n1. If the\n2. Which of the"
    opts = ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"]
    assert validate_mcq(bad, opts), "garbage stub must fail"

    good = "Amnesty International is"
    gopts = [
        "an agency of the United Nations to help refugees of civil wars",
        "a global Human Rights Movement",
        "a non-governmental voluntary organization to help very poor people",
        "an inter-governmental agency to cater to medical emergencies in war-ravaged regions",
    ]
    assert not validate_mcq(good, gopts), "short complete stem must pass"

    airports = """Consider the following airports:
1. Donyi Polo Airport
2. Kushinagar International Airport
3. Vijayawada International Airport
In the recent past, which of the above have been constructed as Greenfield projects?"""
    aopts = ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"]
    assert not validate_mcq(airports, aopts), "airport list must pass"

    # Skeptic fixtures: scarred must fail, clean must pass
    scarred_stem = (ROOT / "scripts/fixtures/prelims_structural/2025_q97_scarred.txt").read_text()
    sopts = ["I only", "II only", "Both I and II", "Neither I nor II"]
    reasons = validate_mcq(scarred_stem, sopts)
    assert reasons, "scarred 2025 Q97 must fail inventory"
    assert any(
        r in reasons
        for r in ("ocr_scar_token", "roman_label_as_item", "stub_numbered_lines", "stub_only_item")
    ), reasons

    clean97 = (ROOT / "scripts/fixtures/prelims_structural/2025_q97_stem.txt").read_text()
    assert not validate_mcq(clean97, sopts), "clean 2025 Q97 must pass"

    scarred30 = (ROOT / "scripts/fixtures/prelims_structural/2011_q30_scarred.txt").read_text()
    o30 = ["1 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"]
    r30 = validate_mcq(scarred30, o30)
    assert r30, "scarred 2011 Q30 must fail"
    assert "ocr_scar_token" in r30 or "false_qnum_list_break" in r30, r30

    clean30 = (ROOT / "scripts/fixtures/prelims_structural/2011_q30_stem.txt").read_text()
    assert not validate_mcq(clean30, o30), "clean 2011 Q30 must pass"

    trunc_opts = [
        "Uplift of folded Himalayan series",
        "Syntaxial bending of geologically young Himalayas",
        "Geo-tectonic disturbance in the tertiary folded mountain chains",
        "Both (A) and",
    ]
    assert "option_truncated_3" in validate_mcq(
        "The Brahmaputra makes a U turn due to", trunc_opts
    )


def test_skeptic_2025_q97_and_2011_gaps_clean_in_bank():
    """Prior skeptic gaps must be clean in shipped banks."""
    from prelims_mcq_complete import validate_mcq

    checks = [
        (2025, 97, ["Anadyr", "Nome", "these cities"], [r"(?m)^\s*1\.\s*i\.", r"\bthee\b"]),
        (2011, 30, ["up to two children", "classes 9 and 12"], [r"\butwo\b", r"(?m)^\s*12\.\s*Which"]),
        (
            2011,
            97,
            ["these rivers", "flow through", "Both (a) and (b)"],
            [r"\bthee\b", r"flow it through", r"Both\s*\([ABab]\)\s*and\s*$"],
        ),
    ]
    import re

    for year, num, musts, forbiddens in checks:
        data = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())
        q = data["questions"][num - 1]
        stem = q["question"]
        joined = stem + "\n" + "\n".join(o.get("text") or "" for o in q["options"])
        for m in musts:
            assert m.lower() in joined.lower(), (year, num, m, joined[:200])
        for f in forbiddens:
            assert not re.search(f, joined, re.I | re.M), (year, num, f, joined[:200])
        reasons = validate_mcq(stem, q["options"])
        assert not reasons, (year, num, reasons, stem[:120])
        assert q.get("correctAnswers")


def test_ocr_mash_and_match_matrix_fixtures_fail():
    """Honest fixtures for skeptic garbage must fail both gates."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars

    cases = [
        ("2013_q84_scarred.txt", "2013_q84_scarred_opts.json"),
        ("2011_q54_scarred.txt", "2011_q54_scarred_opts.json"),
        ("2012_q85_scarred.txt", "2012_q85_scarred_opts.json"),
        ("2026_match_scarred.txt", "2026_match_scarred_opts.json"),
    ]
    fix = ROOT / "scripts/fixtures/prelims_structural"
    for stem_name, opts_name in cases:
        stem = (fix / stem_name).read_text()
        opts = json.loads((fix / opts_name).read_text())
        vr = validate_mcq(stem, opts)
        sr = high_severity_scars(stem, opts)
        assert vr or sr, (stem_name, "must fail at least one gate", vr, sr)


def test_skeptic_ocr_mash_static_qs_clean():
    """Previously shipped unreadable MCQs must now be coherent English."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars

    checks = [
        (2018, 36, ["microbeads"], ["fefred", "haat"]),
        (2017, 59, ["DigiLocker", "Digital India"], ["NSQFY", "frafafad", "aa 1"]),
        (2019, 37, ["Borobudur", "Angkor"], ["fefafar"]),
        (2016, 9, ["Krishna Deva", "Vijayanagar"], ["conaider", "wqrkshops", "Wllich"]),
        (2023, 66, ["Carbon fibres"], ["iffi", "Uf.ftfij"]),
        (2023, 78, ["mercury pollution"], ["fdJ", "\\\\f"]),
        (2013, 84, ["Regional Rural Banks", "Land Development"], ["aay aH", "shteht"]),
        (2011, 54, ["Quit India"], ["Comwallis", "teason", "vis-a-viy"]),
        (2012, 85, ["Eight Core Industries", "Cement", "Fertilizers"], ["tridice", "Gément", "Fertitizers"]),
        (2026, 56, ["Mangdechhu", "Codes (A B C D)"], ["Code: A B C D a)"]),
        (2026, 80, ["BIMSTEC Energy Centre"], ["Code: A B C D"]),
        (2026, 37, ["INTERPOL", "Silver Notice"], ["Code: A B C D a)"]),
        (2026, 60, ["Rare Earth", "National Critical Mineral"], ["Ministry of Ports"]),
        (2026, 74, ["Deep Ocean Mission", "Matsya-6000", "Earth Sciences"], ["Ministry of Ports"]),
        (2011, 53, ["Cornwallis", "None of the (a), (b) and (c)"], [r"^None of the \(a\),\s*$"]),
        (2012, 25, ["Congress ministries", "None of the statements (a), (b) and (c)"], [r"^None of the statements \(a\),\s*$"]),
        (2012, 36, ["Communal Award"], [r"^None of the statements \(a\),\s*$"]),
    ]
    import re

    for year, num, musts, forbiddens in checks:
        data = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())
        q = data["questions"][num - 1]
        joined = q["question"] + "\n" + "\n".join(o.get("text") or "" for o in q["options"])
        for m in musts:
            assert m.lower() in joined.lower(), (year, num, m, joined[:160])
        for f in forbiddens:
            if f.startswith("^") or "\\" in f:
                # per-option regex (truncated option must not appear alone)
                for o in q["options"]:
                    assert not re.search(f, (o.get("text") or "").strip(), re.I), (
                        year,
                        num,
                        f,
                        o.get("text"),
                    )
            else:
                assert f.lower() not in joined.lower(), (year, num, f, joined[:160])
        assert not validate_mcq(q["question"], q["options"]), (year, num, validate_mcq(q["question"], q["options"]))
        assert not high_severity_scars(q["question"], q["options"]), (
            year,
            num,
            high_severity_scars(q["question"], q["options"]),
        )
        assert q.get("correctAnswers")


def test_modular_rules_fail_skeptic_fixtures():
    """Fixture-first: exact skeptic scarred snippets must fail validate_mcq."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars

    fix = ROOT / "scripts/fixtures/prelims_regression"
    cases = [
        ("2012_q89_scarred.txt", "2012_q89_opts.json"),
        ("2014_q37_scarred.txt", "2014_q37_opts.json"),
        ("2016_q86_scarred.txt", "2016_q86_opts.json"),
        ("2026_q97_scarred.txt", "2026_q97_opts.json"),
    ]
    for stem_n, opts_n in cases:
        stem = (fix / stem_n).read_text()
        opts = json.loads((fix / opts_n).read_text())
        vr = validate_mcq(stem, opts)
        assert vr, (stem_n, "must fail validate_mcq")
    # option-only chrome fixtures
    stem = "Which of the statements given above is/are correct?"
    assert validate_mcq(stem, json.loads((fix / "2015_q3_opts.json").read_text()))
    assert validate_mcq(stem, json.loads((fix / "2021_q63_opts.json").read_text()))
    assert validate_mcq(stem, json.loads((fix / "2024_answer_x_opts.json").read_text()))
    # high_severity also catches answer chrome
    assert high_severity_scars(
        stem, json.loads((fix / "2024_answer_x_opts.json").read_text())
    )


def test_prelims_regression_manifest_clean():
    """Every skeptic-refuted (year,num) must be clean in static banks."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars

    manifest = ROOT / "scripts/fixtures/prelims_regression/manifest.jsonl"
    rows = [
        json.loads(line)
        for line in manifest.read_text().splitlines()
        if line.strip()
    ]
    assert len(rows) >= 10
    for row in rows:
        year, num = int(row["year"]), int(row["num"])
        data = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())
        q = data["questions"][num - 1]
        key = row.get("key") or ""
        if key:
            assert key.lower().split()[0] in q["question"].lower() or any(
                w.lower() in q["question"].lower() for w in key.split()[:2]
            ), (year, num, key, q["question"][:80])
        reasons = validate_mcq(q["question"], q["options"])
        scars = high_severity_scars(q["question"], q["options"])
        assert not reasons, (year, num, reasons, q["question"][:100])
        assert not scars, (year, num, scars)
        assert q.get("correctAnswers")
        for o in q["options"]:
            t = o.get("text") or ""
            assert "Answer: X" not in t
            assert "Ans)" not in t
            assert "ronly" not in t.lower()
            assert not t.strip().endswith("and.")


def test_assertion_reason_scarred_fixtures_fail():
    """A/R OCR + off-topic options must fail inventory (skeptic CV37)."""
    from prelims_mcq_complete import validate_mcq

    fix = ROOT / "scripts/fixtures/prelims_regression"
    for stem_n, opts_n, must_reason in [
        ("2023_q85_scarred.txt", "2023_q85_scarred_opts.json", "ar_options_off_topic"),
        ("2023_q93_scarred.txt", "2023_q93_scarred_opts.json", "ar_options_off_topic"),
        ("2023_q28_scarred.txt", "2023_q28_scarred_opts.json", "ar_ocr_scar"),
        ("2024_q21_scarred.txt", "2024_q21_scarred_opts.json", "ar_truncated_statement"),
    ]:
        stem = (fix / stem_n).read_text()
        opts = json.loads((fix / opts_n).read_text())
        reasons = validate_mcq(stem, opts)
        assert reasons, (stem_n, "must fail")
        assert any(
            must_reason in r or r.startswith("ar_") or r == "ocr_scar_token" or r == "prompt_as_numbered_item"
            for r in reasons
        ), (stem_n, reasons)


def test_convert_preserves_assertion_reason_stem():
    """Convert must not renumber Statement-I/II into 1./2./3.Which…"""
    import importlib.util

    conv_path = ROOT / "scripts" / "convert_upsc_to_banks.py"
    spec = importlib.util.spec_from_file_location("convert_upsc_to_banks", conv_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    stem = (
        "Consider the following statements:\n\n"
        "Statement-I: In the post-pandemic recent past, many Central Banks worldwide "
        "had carried out interest rate hikes.\n"
        "Statement-II: Central Banks generally assume that they have the ability to "
        "counteract the rising consumer prices via monetary policy means.\n\n"
        "Which one of the following is correct in respect of the above statements?"
    )
    opts = [
        {"id": "A", "text": "Both Statement-I and Statement-II are correct and Statement-II is the correct explanation for Statement-I"},
        {"id": "B", "text": "Both Statement-I and Statement-II are correct and Statement-II is not the correct explanation for Statement-I"},
        {"id": "C", "text": "Statement-I is correct but Statement-II is incorrect"},
        {"id": "D", "text": "Statement-I is incorrect but Statement-II is correct"},
    ]
    q = {
        "question": stem,
        "content": [{"type": "paragraph", "text": stem}],
        "options": opts,
        "answer": {"type": "single", "correct": ["A"]},
    }
    built = mod.build_stem(q)
    assert "Statement-I:" in built
    assert "Statement-II:" in built
    assert "1. Statement-I" not in built
    assert "3. Which" not in built
    out = mod.convert_question(q, "upsc_2023_gs1", mod.PAPER_META[("PRELIMS", "GS1")], 28)
    assert "1. Statement-I" not in out[0]["question"]
    assert "3. Which" not in out[0]["question"]
    assert "Central Banks" in out[0]["question"]


def test_option_stem_ocr_glitch_fixtures_fail():
    """cexplanation / is are / noé / tis own / pubic sectore must fail inventory."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars

    fix = ROOT / "scripts/fixtures/prelims_regression"
    # option OCR
    opts = json.loads((fix / "2023_q15_scarred_opts.json").read_text())
    r = validate_mcq(
        "Which one of the following is correct in respect of the above statements?",
        opts,
    )
    assert "ocr_scar_token" in r or any("ocr" in x for x in r), r
    opts61 = json.loads((fix / "2024_q61_scarred_opts.json").read_text())
    r61 = validate_mcq(
        "Which one of the following is correct in respect of the above statements?",
        opts61,
    )
    assert r61, r61
    r77 = validate_mcq(
        (fix / "2019_q77_scarred.txt").read_text(),
        json.loads((fix / "2019_q77_scarred_opts.json").read_text()),
    )
    assert "ocr_scar_token" in r77, r77
    r29 = validate_mcq(
        (fix / "2024_q29_scarred.txt").read_text(),
        json.loads((fix / "2024_q29_scarred_opts.json").read_text()),
    )
    assert "ocr_scar_token" in r29, r29
    # legitimate is/are must pass
    assert not validate_mcq(
        "Which of the statements given above is/are correct?",
        ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    )


def test_skeptic_ocr_glitch_static_clean():
    """Shipped banks must not contain cexplanation/is-are/noé/tis-own/pubic."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars
    import re

    ban = re.compile(
        r"(?i)cexplanation|\bis are\b|no[eé]\s+explain|\btis own\b|pubic sectore|correct A\)\s*$"
    )
    checks = [
        (2023, 15, "greenhouse"),
        (2024, 29, "its own"),
        (2024, 61, "Carbon Border"),
        (2019, 77, "public sector"),
    ]
    for year, num, must in checks:
        q = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())[
            "questions"
        ][num - 1]
        joined = q["question"] + "\n" + "\n".join(o.get("text") or "" for o in q["options"])
        assert must.lower() in joined.lower(), (year, num, must)
        assert not ban.search(joined), (year, num, ban.search(joined))
        assert not validate_mcq(q["question"], q["options"])
        assert not high_severity_scars(q["question"], q["options"])


def test_iter_look_east_scarred_fixtures_fail():
    """ITER option mash and Look East OCR stems must fail inventory."""
    from prelims_mcq_complete import validate_mcq

    fix = ROOT / "scripts/fixtures/prelims_regression"
    r79 = validate_mcq(
        (fix / "2016_q79_scarred.txt").read_text(),
        json.loads((fix / "2016_q79_scarred_opts.json").read_text()),
    )
    assert r79, "ITER scarred must fail"
    assert "ocr_scar_token" in r79 or any("ocr" in x for x in r79), r79
    r42 = validate_mcq(
        (fix / "2011_q42_scarred.txt").read_text(),
        json.loads((fix / "2011_q42_scarred_opts.json").read_text()),
    )
    assert r42 and "ocr_scar_token" in r42, r42
    # clean vacuum must pass (not false-positive on 'vacuum')
    clean = (
        "India wants to plug the vacuum created by the termination of the Cold War."
    )
    assert not validate_mcq(
        clean,
        ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
    )


def test_iter_look_east_static_clean():
    """Shipped ITER and Look East Qs must be readable English."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars
    import re

    ban = re.compile(
        r"(?i)vacuu\b|Col War|neighbow|usc thorium|pow or|Chehrisford|"
        r"satellite navigation fol|\bKk is\b|_ experiment"
    )
    checks = [
        (2011, 42, "Cold War"),
        (2016, 13, "Combat Desertification"),
        (2016, 76, "Atal Pension"),
        (2016, 75, "fusion reactors"),  # clean ITER slot
        (2025, 5, "1961"),
    ]
    for year, num, must in checks:
        q = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())[
            "questions"
        ][num - 1]
        joined = q["question"] + "\n" + "\n".join(o.get("text") or "" for o in q["options"])
        assert must.lower() in joined.lower(), (year, num, must, joined[:120])
        assert not ban.search(joined), (year, num, ban.search(joined))
        assert not validate_mcq(q["question"], q["options"]), (
            year,
            num,
            validate_mcq(q["question"], q["options"]),
        )
        assert not high_severity_scars(q["question"], q["options"])


def test_prompt_as_item_and_ocr_typo_fixtures_fail():
    """Skeptic CV40 scars: prompt-as-item, Statements-I, Selected Corrected, remammg."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars

    fix = ROOT / "scripts/fixtures/prelims_regression"
    cases = [
        ("2018_q32_scarred.txt", "2018_q32_scarred_opts.json", "prompt_as_numbered_item"),
        ("2024_q5_scarred.txt", "2024_q5_scarred_opts.json", "prompt_as_numbered_item"),
        ("2023_q14_scarred.txt", "2023_q14_scarred_opts.json", "ar_numbered_statements_label"),
        ("2019_q57_scarred.txt", "2019_q57_scarred_opts.json", "ocr_scar_token"),
        ("2013_q85_scarred.txt", "2013_q85_scarred_opts.json", "ocr_scar_token"),
        ("2016_q63_scarred.txt", "2016_q63_scarred_opts.json", "ocr_scar_token"),
    ]
    for st, op, need in cases:
        stem = (fix / st).read_text()
        opts = json.loads((fix / op).read_text())
        r = validate_mcq(stem, opts)
        assert r, (st, "must fail validate")
        assert need in r or any(
            x in r
            for x in (
                "prompt_as_numbered_item",
                "ar_numbered_statements_label",
                "ocr_scar_token",
                "option_ocr_glitch_0",
                "option_ocr_glitch_3",
            )
        ), (st, need, r)
        # at least one of validate or high_severity must fire
        sr = high_severity_scars(stem, opts)
        assert r or sr, (st, r, sr)
    # year.Which must NOT false-flag
    stem_year = (
        "Consider the following statements:\n"
        "1. The SDGs have to be achieved by\n"
        "2030. Which of the statements given above is/are correct?"
    )
    assert "prompt_as_numbered_item" not in validate_mcq(
        stem_year, ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"]
    )


def test_skeptic_cv40_static_clean():
    """Shipped banks for skeptic CV40 IDs must be clean English."""
    from prelims_mcq_complete import validate_mcq
    from prelims_quality import high_severity_scars
    import re

    ban = re.compile(
        r"Which of following statements given above|"
        r"^\s*[1-9]\.\s*Which of the statement|"
        r"Statements\s*-\s*I\s*:|Selected the Corrected|"
        r"\bremammg\b|\bimitative\b|Frontiercs|rewarding the Maternity|"
        r"passes by the|Neither 1 Or 2|\b1and 2\b",
        re.I | re.M,
    )
    checks = [
        (2018, 32, "President of India"),
        (2024, 5, "Prorogation"),
        (2024, 98, "PFAS"),
        (2023, 14, "InvITs"),
        (2019, 57, "Maternity Benefit"),
        (2019, 75, "VoLTE"),
        (2013, 28, "Economic Justice"),
        (2013, 85, "remaining the same"),
        (2016, 51, "Frontieres"),
        (2016, 63, "initiative"),
        (2016, 93, "is passed by"),
        (2017, 85, "Rights are claims"),
        (2017, 100, "SANKALP"),
    ]
    for year, num, must in checks:
        q = json.loads((ROOT / f"static/upsc/prelims-gs1/{year}.json").read_text())[
            "questions"
        ][num - 1]
        joined = q["question"] + "\n" + "\n".join(o.get("text") or "" for o in q["options"])
        assert must.lower() in joined.lower(), (year, num, must, joined[:100])
        assert not ban.search(joined), (year, num, ban.search(joined))
        assert not validate_mcq(q["question"], q["options"])
        assert not high_severity_scars(q["question"], q["options"])
    # 2017 Q85 and Q100 not identical
    d = json.loads((ROOT / "static/upsc/prelims-gs1/2017.json").read_text())
    assert d["questions"][84]["question"] != d["questions"][99]["question"]


def test_convert_does_not_import_repair_stem():
    """Convert must not re-mangle clean prelims via repair_stem surgery."""
    import re

    src = (ROOT / "scripts" / "convert_upsc_to_banks.py").read_text()
    assert "repair_stem" not in src
    assert re.search(r"CONTENT_VERSION\s*=\s*\d+", src)


if __name__ == "__main__":

    test_vitasta_scar_detected_and_repaired()
    test_eu_unnumbered_repaired()
    test_inline_numbered_to_multiline()
    test_already_numbered_not_destroyed()
    test_select_glued_fix()
    test_count_numbered()
    test_static_prelims_zero_high_severity_scars()
    test_convert_preserves_numbered_vitasta_stem()
    test_detects_two_topic_interleave()
    test_detects_word_split_airport_list()
    test_detects_web_chrome_option()
    test_skeptic_flagged_static_qs_clean()
    test_detects_false_number_and_fragments()
    test_skeptic_round3_static_clean()
    test_static_prelims_inventory_empty()
    test_validate_mcq_catches_real_garbage()
    test_skeptic_2025_q97_and_2011_gaps_clean_in_bank()
    test_ocr_mash_and_match_matrix_fixtures_fail()
    test_skeptic_ocr_mash_static_qs_clean()
    test_modular_rules_fail_skeptic_fixtures()
    test_prelims_regression_manifest_clean()
    test_assertion_reason_scarred_fixtures_fail()
    test_convert_preserves_assertion_reason_stem()
    test_option_stem_ocr_glitch_fixtures_fail()
    test_skeptic_ocr_glitch_static_clean()
    test_iter_look_east_scarred_fixtures_fail()
    test_iter_look_east_static_clean()
    test_prompt_as_item_and_ocr_typo_fixtures_fail()
    test_skeptic_cv40_static_clean()
    test_convert_does_not_import_repair_stem()
    print("ALL prelims_quality unit tests PASSED")
