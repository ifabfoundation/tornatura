#!/usr/bin/env python3
"""
Update ObservationType.locationAndScoreInstructions from typology values found in MongoDB.

The script:
- reads the distinct typology values present in the observation_type collection
- tries to resolve each typology to one of the known instruction URLs
- prints a resolution report
- optionally updates matching ObservationType documents
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from collections import Counter

from mongoengine import connect

from core.config import APIConfig
from core.models import ObservationType


INSTRUCTION_URLS = {
    "autographa_gamma": "https://www.tornatura.it/instructions/260520-autographa-gamma?partial=1",
    "cimice_asiatica": "https://www.tornatura.it/instructions/260310-cimice-asiatica?partial=1",
    "diabrotica": "https://www.tornatura.it/instructions/260310-diabrotica?partial=1",
    "giallumi": "https://www.tornatura.it/instructions/260310-giallumi?partial=1",
    "lisso": "https://www.tornatura.it/instructions/260310-lisso?partial=1",
    "mamestre_brassica": "https://www.tornatura.it/instructions/260520-mamestre-brassica?partial=1",
    "mosca_della_frutta": "https://www.tornatura.it/instructions/260527-mosca-della-frutta?partial=1",
    "mosca_dell_olivo": "https://www.tornatura.it/instructions/260527-mosca-dell-olivo?partial=1",
    "peronospora": "https://www.tornatura.it/instructions/260310-peronospora?partial=1",
    "scafoideo": "https://www.tornatura.it/instructions/260310-scafoideo?partial=1",
    "spodoptera_exigua": "https://www.tornatura.it/instructions/260520-spodoptera-exigua?partial=1",
    "cleono": "https://www.tornatura.it/instructions/260513-cleono?partial=1",
    "tignola_del_pesco": "https://www.tornatura.it/instructions/260604-tignola-del-pesco?partial=1",
    "tignola_dell_olivo": "https://www.tornatura.it/instructions/260527-tignola-dell-olivo?partial=1",
    "tignola_orientale_del_pesco": "https://www.tornatura.it/instructions/260604-tignola-orientale-del-pesco?partial=1",
}

TYPOLOGY_ALIASES = {
    "autographa_gamma": {
        "autographa gamma",
    },
    "cimice_asiatica": {
        "cimice",
        "cimice asiatica",
        "halyomorpha halys",
    },
    "diabrotica": {
        "diabrotica",
    },
    "giallumi": {
        "giallumi",
        "flavescenza",
        "flavescenza dorata",
        "fitoplasmi",
    },
    "lisso": {
        "lisso",
    },
    "mamestre_brassica": {
        "mamestre brassica",
        "mamestra brassicae",
    },
    "mosca_della_frutta": {
        "mosca della frutta",
        "ceratitis capitata",
    },
    "mosca_dell_olivo": {
        "mosca dell olivo",
        "mosca dell'olivo",
        "bactrocera oleae",
    },
    "peronospora": {
        "peronospora",
        "fungo e peronospora",
        "funghi e peronospora",
    },
    "scafoideo": {
        "scafoideo",
        "scaphoideus titanus",
        "scaphoideo",
    },
    "tutorial_dati_rilevamento": {
        "tutorial dati rilevamento",
        "tutorial rilevamento",
        "dati rilevamento",
    },
    "multi_insetto": {
        "multi insetto",
        "multiinsetto",
        "rilevamento multiplo",
    },
    "spodoptera_exigua": {
        "spodoptera exigua",
    },
    "tignola_del_pesco": {
        "tignola del pesco",
    },
    "tignola_dell_olivo": {
        "tignola dell olivo",
        "tignola dell'olivo",
        "prays oleae",
    },
    "tignola_orientale_del_pesco": {
        "tignola orientale del pesco",
    },
    "cleono": {
        "cleono",
    },
}


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def normalize(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower().strip()
    cleaned = []
    previous_was_space = False
    for char in normalized:
        if char.isalnum():
            cleaned.append(char)
            previous_was_space = False
        else:
            if not previous_was_space:
                cleaned.append(" ")
                previous_was_space = True
    return "".join(cleaned).strip()


NORMALIZED_ALIAS_TO_KEY = {
    normalize(alias): key
    for key, aliases in TYPOLOGY_ALIASES.items()
    for alias in aliases
}


def resolve_typology(typology: str) -> str | None:
    normalized = normalize(typology)
    if normalized in NORMALIZED_ALIAS_TO_KEY:
        return NORMALIZED_ALIAS_TO_KEY[normalized]

    tokens = set(normalized.split())
    if {"cimice", "asiatica"}.issubset(tokens) or "halyomorpha" in tokens:
        return "cimice_asiatica"
    if "diabrotica" in tokens:
        return "diabrotica"
    if "giallumi" in tokens or "flavescenza" in tokens or "fitoplasmi" in tokens:
        return "giallumi"
    if "autographa" in tokens and "gamma" in tokens:
        return "autographa_gamma"
    if "lisso" in tokens:
        return "lisso"
    if ("mamestre" in tokens or "mamestra" in tokens) and (
        "brassica" in tokens or "brassicae" in tokens
    ):
        return "mamestre_brassica"
    if {"mosca", "frutta"}.issubset(tokens) or {"ceratitis", "capitata"}.issubset(tokens):
        return "mosca_della_frutta"
    if {"mosca", "olivo"}.issubset(tokens) or {"bactrocera", "oleae"}.issubset(tokens):
        return "mosca_dell_olivo"
    if "peronospora" in tokens:
        return "peronospora"
    if "scafoideo" in tokens or "scaphoideus" in tokens or "scaphoideo" in tokens:
        return "scafoideo"
    if "spodoptera" in tokens and "exigua" in tokens:
        return "spodoptera_exigua"
    if "tutorial" in tokens and "rilevamento" in tokens:
        return "tutorial_dati_rilevamento"
    if {"tignola", "pesco"}.issubset(tokens) and "orientale" not in tokens:
        return "tignola_del_pesco"
    if {"tignola", "olivo"}.issubset(tokens) or {"prays", "oleae"}.issubset(tokens):
        return "tignola_dell_olivo"
    if {"tignola", "orientale", "pesco"}.issubset(tokens):
        return "tignola_orientale_del_pesco"
    if "multi" in tokens and "insetto" in tokens:
        return "multi_insetto"
    if "cleono" in tokens:
        return "cleono"
    return None


def build_typology_report() -> list[dict]:
    collection = ObservationType._get_collection()
    pipeline = [
        {"$group": {"_id": "$typology", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    report = []
    for item in collection.aggregate(pipeline):
        typology = item["_id"]
        mapped_key = resolve_typology(typology)
        report.append(
            {
                "typology": typology,
                "count": item["count"],
                "instruction_key": mapped_key,
                "instruction_url": INSTRUCTION_URLS.get(mapped_key) if mapped_key else None,
            }
        )
    return report


def print_report(report: list[dict]) -> None:
    print("ObservationType typology mapping report:")
    unresolved = 0
    for item in report:
        typology = item["typology"]
        count = item["count"]
        url = item["instruction_url"]
        if url:
            print(f"- {typology!r} ({count}) -> {url}")
        else:
            unresolved += 1
            print(f"- {typology!r} ({count}) -> UNRESOLVED")
    print(f"Resolved={len(report) - unresolved}, Unresolved={unresolved}")


def apply_updates(report: list[dict], only_typology: str | None) -> int:
    collection = ObservationType._get_collection()
    updated_docs = 0
    updated_typologies = 0
    changed_urls = Counter()

    for item in report:
        typology = item["typology"]
        url = item["instruction_url"]
        if not url:
            continue
        if only_typology and normalize(typology) != normalize(only_typology):
            continue

        result = collection.update_many(
            {
                "typology": typology,
                "locationAndScoreInstructions": {"$ne": url},
            },
            {"$set": {"locationAndScoreInstructions": url}},
        )
        if result.modified_count > 0:
            updated_typologies += 1
            updated_docs += result.modified_count
            changed_urls[url] += result.modified_count

    print(
        "ObservationType instruction link update: "
        f"updated_typologies={updated_typologies}, updated_docs={updated_docs}"
    )
    if changed_urls:
        print("Updated URLs:")
        for url, count in changed_urls.items():
            print(f"- {url}: {count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update ObservationType instruction links based on typology values found in DB."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to MongoDB. Without this flag, the script only prints the mapping report.",
    )
    parser.add_argument(
        "--typology",
        help="Restrict the update to a single typology value as stored in DB.",
    )
    args = parser.parse_args()

    connect_db()
    report = build_typology_report()
    print_report(report)

    unresolved = [item for item in report if not item["instruction_url"]]
    if unresolved:
        print("Some typologies could not be resolved automatically in this script.")

    if not args.apply:
        print("Dry run only. Re-run with --apply to persist changes.")
        return 0

    return apply_updates(report, only_typology=args.typology)


if __name__ == "__main__":
    sys.exit(main())
