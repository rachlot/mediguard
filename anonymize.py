import openai
import os
import requests
from bs4 import BeautifulSoup

openai.api_key = os.getenv("OPENAI_API_KEY")

def fetch_cirs_data():
    url = "https://www.cirsmedical.ch/AINS/m_files/cirs.php?seitennr=AINS"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    cases = []
    for case in soup.find_all('div', class_='cirs-case'):
        title = case.find('h2').text.strip()
        description = case.find('p').text.strip()
        cases.append({"title": title, "description": description})

    return cases

def detect_names_and_location(full_report):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Du bist ein hilfreicher Assistent im Gesundheitswesen. "
                "Deine Aufgabe ist es, alle Personennamen und den Ort des Ereignisses in einem CIRS-Bericht zu identifizieren. "
                "Liste alle gefundenen Namen und den Ort auf."
            )},
            {"role": "user", "content": f"Bericht: {full_report}"}
        ],
        max_tokens=500,
        temperature=0.7,
    )

    content = response['choices'][0]['message']['content'].strip().split('\n')
    names = [line.split(': ')[1] for line in content if line.startswith("Name")]
    location = next((line.split(': ')[1] for line in content if line.startswith("Ort")), "")
    return names, location

def anonymize_cirs_report(full_report):
    system_prompt = (
        "Du bist ein hilfreicher Assistent im Gesundheitswesen. "
        "Deine Aufgabe ist es, CIRS-Berichte (Critical Incident Reporting System) zu anonymisieren, indem du alle persönlichen und sensiblen Informationen entfernst. "
        "Der Bericht sollte so strukturiert sein, dass die Integrität und der Nutzen der Informationen erhalten bleiben, während die Vertraulichkeit aller beteiligten Parteien gewährleistet wird. "
        "Konkret: "
        "1. Entferne alle Namen oder Identifikatoren von Patienten, Gesundheitsdienstleistern oder Institutionen. "
        "2. Stelle sicher, dass alle Daten, Orte oder spezifischen Details, die zur Identifizierung von Personen oder Einrichtungen führen könnten, verallgemeinert werden. "
        "3. Bewahre die wesentlichen Informationen über den Vorfall, einschließlich der Beschreibung des Ereignisses, der Analyse der Ursachen und der vorgeschlagenen Maßnahmen zur Vermeidung zukünftiger Vorfälle. "
        "Der Zweck des CIRS-Berichts besteht darin, sicherheitsrelevante Ereignisse im Gesundheitswesen zu dokumentieren und zu analysieren, um zukünftige Vorfälle zu verhindern. "
        "Die Struktur des Berichts umfasst typischerweise: "
        "- Eine detaillierte Beschreibung des Vorfalls "
        "- Analyse der zugrunde liegenden Ursachen "
        "- Empfehlungen oder ergriffene Maßnahmen zur Vermeidung ähnlicher Vorfälle in der Zukunft "
        "Stelle sicher, dass der Bericht klar, prägnant und nützlich bleibt, um aus den Ereignissen zu lernen und die Sicherheitspraktiken im Gesundheitswesen zu verbessern."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Anonymisiere diesen Bericht: {full_report}"}
        ],
        max_tokens=500,
        temperature=0.7,
    )

    anonymized_report = response['choices'][0]['message']['content'].strip()

    details_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Du bist ein hilfreicher Assistent im Gesundheitswesen. "
                "Deine Aufgabe ist es, die Details aus anonymisierten CIRS-Berichten zu extrahieren und vorauszufüllen. "
                "Die Struktur des Berichts umfasst typischerweise: "
                "- Eine detaillierte Beschreibung des Vorfalls "
                "- Analyse der zugrunde liegenden Ursachen "
                "- Empfehlungen oder ergriffene Maßnahmen zur Vermeidung ähnlicher Vorfälle in der Zukunft. "
                "Stelle sicher, dass die extrahierten Informationen klar, prägnant und nützlich sind, um aus den Ereignissen zu lernen und die Sicherheitspraktiken im Gesundheitswesen zu verbessern."
            )},
            {"role": "user", "content": f"Extrahiere die Details aus diesem Bericht: {anonymized_report}"}
        ],
        max_tokens=500,
        temperature=0.7,
    )

    details = details_response['choices'][0]['message']['content'].strip()
    details_dict = parse_details(details)

    cirs_cases = fetch_cirs_data()
    cirs_context = "\n".join([f"Fall: {case['title']}\nBeschreibung: {case['description']}" for case in cirs_cases])

    cirs_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Du bist ein hilfreicher Assistent im Gesundheitswesen. "
                "Deine Aufgabe ist es, anonymisierte CIRS-Berichte der CIRS-Matrix zuzuordnen. "
                "Die Matrix basiert auf Schadensausmaß und Auftretenswahrscheinlichkeit. "
                "Wähle die am besten passende Stufe aus der Matrix für den folgenden Bericht. "
                "Verwende dabei die folgenden Beispiele aus der CIRS-Falldatenbank als Referenz: "
                f"{cirs_context}"
            )},
            {"role": "user", "content": f"Bericht: {anonymized_report}"}
        ],
        max_tokens=500,
        temperature=0.7,
    )

    cirs_choice = cirs_response['choices'][0]['message']['content'].strip()
    cirs_details = parse_cirs_choice(cirs_choice)

    return anonymized_report, details_dict, cirs_details

def parse_details(details):
    details_dict = {}
    lines = details.split('\n')
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            details_dict[key.replace(' ', '_').lower()] = value
    return details_dict

def parse_cirs_choice(choice):
    lines = choice.split('\n')
    try:
        schaden = lines[0].split(': ')[1].strip()
        wahrscheinlichkeit = lines[1].split(': ')[1].strip()
        return {"schaden": schaden, "wahrscheinlichkeit": wahrscheinlichkeit}
    except IndexError:
        print(f"Fehler beim Parsen der CIRS-Auswahl: {choice}")
        return {"schaden": "", "wahrscheinlichkeit": ""}
