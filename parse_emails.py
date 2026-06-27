#!/usr/bin/env python3
"""
Parse r2-backup/COM/ JSON files and extract unique emails with
associated name, language, geo, and delivery status into emails.csv

Included metrics:  sent, delivered, opened, clicked, converted,
                   subscribed, unsubscribed, dropped (spam)
Excluded metrics:  bounced, attempted, failed, undeliverable, drafted
"""

import csv
import glob
import json
import os
import re
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_GLOB = os.path.join(BASE_DIR, "r2-backup/COM/**/*.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "emails.csv")

# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

LANG_KEYWORDS = {
    "fi": {
        "talletuksesi", "kotiutuksesi", "jääkiekon", "uusi", "tilillesi",
        "unohditko", "salasanasi", "vahvista", "rekisteröitymisesi",
        "asiakirjaasi", "ilmaiskierroksia", "suorita", "tehtäviä", "nappaa",
        "palkintoja", "päivittäiset", "päivitys", "viikoittainen",
        "kasinokoosteesi", "urheilukatsauksesi", "lunasta", "bonuksesi",
        "sinulle", "valitettavasti", "tililläsi",
    },
    "et": {
        "sinu", "sissemakse", "laekunud", "väljavõtutaotlus", "kinnitati",
        "tühistati", "ebaõnnestus", "vabasta", "ärge", "iganädalane",
        "kasiino", "kokkuvõte", "tonybetilt", "võeti", "vastu",
    },
    "ru": {
        "ваш", "депозит", "получен", "запрос", "вывод", "средств",
        "отменён", "удалось", "фриспины", "обновление", "программы",
        "еженедельный", "обзор", "казино", "разблокируй", "бонус",
        "упусти", "добавлен",
    },
    "is": {
        "innborgun", "móttekin", "uppfærsla", "prógrammi", "skjal",
        "samþykkt", "þín",
    },
    "de": {
        "ihre", "einzahlung", "eingegangen", "hinzugefügt", "passwort",
        "zurücksetzen", "verifizierung",
    },
    "fr": {
        "votre", "dépôt", "retrait", "effectué", "approuvée", "demande",
        "récapitulatif", "résumé", "bonjour", "bienvenue", "félicitations",
        "annulée", "confirmez", "inscription", "réinitialiser", "ajouté",
        "veuillez", "jusqu", "encore", "rappel", "defini",
    },
    "es": {
        "nuevo", "juega", "compañía", "suerte", "bono", "depósito",
        "retirada", "solicitud", "recibido", "tienes", "semanal", "aquí",
        "resumen", "fallida", "recibida", "añadido", "confirme", "registro",
        "contraseña", "restablecer", "código", "aprobada", "cancelada",
        "inactiva", "establecido", "alerta", "desactivacion", "establecido",
        "giros", "misiones", "premios",
    },
}


def detect_lang(subject: str) -> str:
    s = subject.lower()
    # Cyrillic → Russian
    if re.search(r"[а-яё]", s):
        return "ru"
    tokens = set(re.findall(r"[\w\-]+", s, re.UNICODE))
    for lang, kw in LANG_KEYWORDS.items():
        if tokens & kw:
            return lang
    return "en"


# ---------------------------------------------------------------------------
# Geo detection
# ---------------------------------------------------------------------------

CCTLD = {
    "ca": "Canada",   "fr": "France",      "ie": "Ireland",
    "es": "Spain",    "mx": "Mexico",      "ar": "Argentina",
    "br": "Brazil",   "pt": "Portugal",    "de": "Germany",
    "it": "Italy",    "nl": "Netherlands", "be": "Belgium",
    "ch": "Switzerland", "at": "Austria",  "pl": "Poland",
    "cz": "Czechia",  "sk": "Slovakia",    "hu": "Hungary",
    "ro": "Romania",  "bg": "Bulgaria",    "hr": "Croatia",
    "lt": "Lithuania","lv": "Latvia",      "ee": "Estonia",
    "fi": "Finland",  "se": "Sweden",      "no": "Norway",
    "dk": "Denmark",  "gb": "United Kingdom", "uk": "United Kingdom",
    "ru": "Russia",   "ua": "Ukraine",     "by": "Belarus",
    "au": "Australia","nz": "New Zealand", "za": "South Africa",
    "in": "India",    "jp": "Japan",       "cn": "China",
    "kr": "South Korea", "is": "Iceland",  "cl": "Chile",
    "co": "Colombia", "pe": "Peru",        "ve": "Venezuela",
    "ec": "Ecuador",  "uy": "Uruguay",     "py": "Paraguay",
    "bo": "Bolivia",  "do": "Dominican Republic",
}

# Explicit domain → country (overrides TLD logic)
DOMAIN_GEO = {
    # Canada ISPs
    "telus.net": "Canada",       "telusplanet.net": "Canada",
    "shaw.ca": "Canada",         "rogers.com": "Canada",
    "bell.net": "Canada",        "sympatico.ca": "Canada",
    "videotron.ca": "Canada",    "eastlink.ca": "Canada",
    "sasktel.net": "Canada",     "mta.ca": "Canada",
    "yvonroyinc.com": "Canada",
    # Estonia
    "mail.ee": "Estonia",        "hot.ee": "Estonia",
    "kmoy.ee": "Estonia",
    # Russia
    "mail.ru": "Russia",         "list.ru": "Russia",
    "bk.ru": "Russia",           "inbox.ru": "Russia",
    # Finland
    "netti.fi": "Finland",       "luukku.com": "Finland",
    "elisanet.fi": "Finland",    "saunalahti.fi": "Finland",
    "wippies.fi": "Finland",     "phpoint.fi": "Finland",
    "kolumbus.fi": "Finland",    "nettiviisi.fi": "Finland",
    # Latvia/Lithuania
    "inbox.lv": "Latvia",        "inbox.lt": "Lithuania",
    # Ireland
    "rcsi.ie": "Ireland",        "ymca-ireland.net": "Ireland",
    # Other
    "wp.pl": "Poland",           "mailxsx.com": "Unknown geo",
    "privaterelay.appleid.com": "Unknown geo",
}

GEO_SUBJECTS = {
    "alberta": "Canada",   "ontario": "Canada",    "quebec": "Canada",
    "british columbia": "Canada", "nova scotia": "Canada",
    "manitoba": "Canada",  "saskatchewan": "Canada",
}

# SMS country-code prefix → country
PHONE_PREFIX = {
    "+358": "Finland",  "+372": "Estonia",  "+7":   "Russia",
    "+354": "Iceland",  "+49":  "Germany",  "+33":  "France",
    "+34":  "Spain",    "+56":  "Chile",    "+353": "Ireland",
    "+44":  "United Kingdom",  "+61": "Australia",
    "+64":  "New Zealand",
}


def detect_geo_from_phone(phone: str) -> str:
    for prefix, country in sorted(PHONE_PREFIX.items(), key=lambda x: -len(x[0])):
        if phone.startswith(prefix):
            return country
    if phone.startswith("+1"):
        return "North America"  # USA or Canada — can't distinguish by prefix alone
    return ""


def detect_geo(email: str, subjects: list) -> str:
    combined = " ".join(subjects).lower()
    for kw, country in GEO_SUBJECTS.items():
        if kw in combined:
            return country

    if "@" not in email:
        return "Unknown geo"

    domain = email.split("@")[1].lower()

    if domain in DOMAIN_GEO:
        geo = DOMAIN_GEO[domain]
        return geo if geo else "Unknown geo"

    # Subdomain check: hotmail.fr → .fr, yahoo.ca → .ca, etc.
    parts = domain.split(".")
    for i in range(len(parts) - 1, 0, -1):
        tld = ".".join(parts[i:])
        if tld in CCTLD:
            return CCTLD[tld]
        if parts[i] in CCTLD:
            return CCTLD[parts[i]]

    return "Unknown geo"


# ---------------------------------------------------------------------------
# Delivery status
# ---------------------------------------------------------------------------

# Metrics we accept (everything else is discarded)
VALID_METRICS = {
    "sent", "delivered", "opened", "clicked", "converted",
    "subscribed", "unsubscribed", "dropped", "spammed",
}

# Priority order for "best status" per email (higher index = better)
STATUS_PRIORITY = [
    "dropped",       # spam — lowest priority, still useful
    "spammed",
    "unsubscribed",
    "subscribed",
    "sent",
    "delivered",
    "opened",
    "clicked",
    "converted",     # highest — confirmed active user
]
STATUS_RANK = {s: i for i, s in enumerate(STATUS_PRIORITY)}

STATUS_LABELS = {
    "sent":         "sent",
    "delivered":    "delivered",
    "opened":       "opened",
    "clicked":      "clicked",
    "converted":    "converted",
    "subscribed":   "subscribed",
    "unsubscribed": "unsubscribed",
    "dropped":      "spam",
    "spammed":      "spam",
}


# ---------------------------------------------------------------------------
# Name extraction
# ---------------------------------------------------------------------------

# Matches "Firstname, <rest of subject>" — supports accented/hyphenated names
NAME_RE = re.compile(
    r"^([A-ZÀ-ÖÙ-ÜÞÐÀ-ž]"     # uppercase first char (incl. extended latin)
    r"[a-zà-öù-üþðÀ-ž\-]{1,29})"  # rest of name
    r",\s"
)


def extract_name(subject: str) -> str:
    m = NAME_RE.match(subject)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    files = glob.glob(INPUT_GLOB, recursive=True)
    total = len(files)
    print(f"Found {total:,} files, processing...", flush=True)

    # email → aggregated data
    by_email: dict[str, dict] = defaultdict(lambda: {
        "names": Counter(),
        "subjects": [],
        "lang_votes": Counter(),
        "best_status_rank": -1,
        "best_status": None,
    })
    # customer_id → set of emails (for cross-referencing names)
    cid_to_emails: dict[str, set] = defaultdict(set)

    skipped = 0

    for i, path in enumerate(files):
        if i % 20000 == 0:
            print(f"  {i:,}/{total:,}", end="\r", flush=True)
        try:
            with open(path) as f:
                obj = json.load(f)
        except Exception:
            continue

        metric = obj.get("metric", "")
        otype = obj.get("object_type", "")
        data = obj.get("data", {})

        # Resolve email
        email = ""
        if otype in ("email", "sms", "push"):
            email = (data.get("recipient") or "").strip().lower()
        elif otype == "customer":
            email = (data.get("email_address") or "").strip().lower()

        # Skip non-email recipients (phone numbers, empty)
        if not email or "@" not in email:
            continue

        # Discard bad-delivery metrics — but still register the email
        # only if it has at least one valid metric event
        if metric not in VALID_METRICS:
            skipped += 1
            # Don't add to by_email at all if we've never seen this email
            # (we process valid events first; invalids are just ignored)
            continue

        subject = (data.get("subject") or "").strip()
        cid = str(data.get("customer_id") or "")

        rec = by_email[email]
        if cid:
            cid_to_emails[cid].add(email)

        # Track best delivery status
        rank = STATUS_RANK.get(metric, -1)
        if rank > rec["best_status_rank"]:
            rec["best_status_rank"] = rank
            rec["best_status"] = metric

        if subject:
            rec["subjects"].append(subject)
            rec["lang_votes"][detect_lang(subject)] += 1
            name = extract_name(subject)
            if name:
                rec["names"][name] += 1

        # Webhook: parse JSON content for title/message to detect language
        if otype == "webhook":
            content_str = data.get("content") or ""
            try:
                content_obj = json.loads(content_str)
                title = content_obj.get("payload", {}).get("title", "")
                if title:
                    rec["lang_votes"][detect_lang(title)] += 1
            except Exception:
                pass

    print(f"\nEvents skipped (bad delivery): {skipped:,}")

    # Second pass: cross-reference names via customer_id
    # Build cid → best name from all emails sharing that cid
    cid_to_name: dict[str, str] = {}
    for cid, emails in cid_to_emails.items():
        merged = Counter()
        for em in emails:
            merged.update(by_email[em]["names"])
        if merged:
            cid_to_name[cid] = merged.most_common(1)[0][0]

    print(f"\nUnique emails: {len(by_email):,}")
    print(f"Writing {OUTPUT_CSV}...")

    # Build reverse index: email → cid (for cross-reference lookup)
    email_to_cid: dict[str, str] = {}
    for cid, emails in cid_to_emails.items():
        for em in emails:
            email_to_cid[em] = cid

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        writer.writerow(["email", "name", "language", "geo"])

        for email, rec in sorted(by_email.items()):
            # Name: prefer most frequent from personalized subjects
            name = "User"
            if rec["names"]:
                name = rec["names"].most_common(1)[0][0]
            else:
                cid = email_to_cid.get(email, "")
                if cid and cid in cid_to_name:
                    name = cid_to_name[cid]

            # Language: majority vote
            language = "unknown language"
            if rec["lang_votes"]:
                language = rec["lang_votes"].most_common(1)[0][0]

            geo = detect_geo(email, rec["subjects"])

            writer.writerow([email, name, language, geo])

    print("Done.")


if __name__ == "__main__":
    main()
