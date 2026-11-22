"""Génère les fichiers agenda/*.ics (un par combinaison de réponses).

Usage : python3 outils/agenda.py   (depuis la racine du dépôt)

Garder les événements en phase avec CONFIG.agenda dans index.html.
"""
from datetime import datetime, timezone, timedelta
from itertools import product
from pathlib import Path

PARIS = timezone(timedelta(hours=2))  # heure d'été (juin)
SITE = "https://lucile-corentin.yoannfradin.fr"
LIGNES = {
    "mairie": "• 26 juin, 14h30 — Mairie d'Avallon, 37 Grande Rue Aristide Briand, 89200 Avallon",
    "eglise": "• 26 juin, 16h30 — Église Collégiale Saint-Lazare, 11 Rue Bocquillot, 89200 Avallon",
    "reception": "• 26 juin, 18h — Réception, Les Gaties, 89630 Saint-Germain-des-Champs",
    "lendemain": "• 27 juin — Anniversaire de Roma, Les Gaties, 89630 Saint-Germain-des-Champs",
}


def details(ids):
    """Description limitée aux moments auxquels l'invité participe."""
    return "Votre programme :\n" + "\n".join(LIGNES[i] for i in ids) + "\n\nPlus d'infos : " + SITE


# id, titre, début, fin, lieu — un début (a, m, j) sans heure = journée entière
EVENTS = {
    "mairie": ("Mariage Lucile & Corentin · Mairie", (2027, 6, 26, 14, 30), (2027, 6, 26, 15, 30),
               "Mairie d'Avallon, 37 Grande Rue Aristide Briand, 89200 Avallon"),
    "eglise": ("Mariage Lucile & Corentin · Église", (2027, 6, 26, 16, 30), (2027, 6, 26, 17, 45),
               "Église Collégiale Saint-Lazare, 11 Rue Bocquillot, 89200 Avallon"),
    "reception": ("Mariage Lucile & Corentin · Réception", (2027, 6, 26, 18, 0), (2027, 6, 27, 2, 0),
                  "Les Gaties, 89630 Saint-Germain-des-Champs"),
    "lendemain": ("Lendemain du mariage · Anniversaire de Roma", (2027, 6, 27), (2027, 6, 28),
                  "Les Gaties, 89630 Saint-Germain-des-Champs"),
}
ORDER = ["mairie", "eglise", "reception", "lendemain"]


def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def when(prop, t):
    if len(t) == 3:
        return f"{prop};VALUE=DATE:{t[0]:04d}{t[1]:02d}{t[2]:02d}"
    return prop + ":" + datetime(*t, tzinfo=PARIS).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def fold(line):
    out, cur = [], b""
    for ch in line:
        c = ch.encode("utf-8")
        if len(cur) + len(c) > 75:
            out.append(cur)
            cur = b" "
        cur += c
    out.append(cur)
    return b"\r\n".join(out).decode("utf-8")


def calendar(ids):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Lucile & Corentin//Mariage//FR",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    for i in ids:
        title, start, end, loc = EVENTS[i]
        lines += ["BEGIN:VEVENT", f"UID:mariage-{i}-20270626@lucile-corentin.yoannfradin.fr",
                  "DTSTAMP:" + stamp, when("DTSTART", start), when("DTEND", end),
                  "SUMMARY:" + esc(title), "LOCATION:" + esc(loc), "DESCRIPTION:" + esc(details(ids)),
                  "URL:" + SITE, "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


out = Path("agenda")
out.mkdir(exist_ok=True)
for mairie, eglise, lendemain in product([True, False], repeat=3):
    ids = [i for i, on in zip(ORDER, [mairie, eglise, True, lendemain]) if on]
    path = out / ("-".join(ids) + ".ics")
    path.write_text(calendar(ids), encoding="utf-8", newline="")
    print(path)
