import requests

url = "http://127.0.0.1:5000/whatsapp"

def simulate(user_number, messages, label):
    print(f"\n--- {label} ---")
    for i, msg in enumerate(messages, 1):
        data = {'Body': msg, 'From': user_number}
        r = requests.post(url, data=data)
        print(f"Étape {i} ({msg!r}):")
        print(r.text)
        print("-" * 40)

# 1. Livraison classique complète
simulate(
    "whatsapp:+221700000001",
    [
        "bonjour",
        "1",
        "Sacré Coeur",
        "Liberté 6",
        "Petit sac à dos beige",
        "Kevin Frederic",
        "789145867",
        "oui"
    ],
    "Test livraison classique"
)

# 2. Livraison repas complète
simulate(
    "whatsapp:+221700000002",
    [
        "bonjour",
        "2",
        "Rafia kitchen",
        "Avorbam",
        "Gueule tapée",
        "Thiaga land",
        "7706960034",
        "234tonculsuceM01",
        "oui"
    ],
    "Test livraison repas"
)

# 3. Livraison entreprise complète
simulate(
    "whatsapp:+221700000003",
    [
        "bonjour",
        "3",
        "Keur Massar",
        "Plateau",
        "Colis informatique x2",
        "14h",
        "771234567",
        "REF-ENT-2024",
        "oui"
    ],
    "Test livraison entreprise"
)

# 4. Annulation à l'étape 2
simulate(
    "whatsapp:+221700000004",
    [
        "bonjour",
        "1",
        "annuler"
    ],
    "Test annulation"
)

# 5. Support à n'importe quel moment
simulate(
    "whatsapp:+221700000005",
    [
        "aide"
    ],
    "Test support"
)

# 6. Suivi avec une référence existante (à adapter selon ton CSV)
simulate(
    "whatsapp:+221700000001",
    [
        "suivi 789145867"
    ],
    "Test suivi existant"
)

# 7. Suivi avec une référence inexistante
simulate(
    "whatsapp:+221700000001",
    [
        "suivi 000000000"
    ],
    "Test suivi inexistant"
)

# 8. Mauvais choix au menu principal
simulate(
    "whatsapp:+221700000006",
    [
        "bonjour",
        "5",  # Choix inexistant
        "classiqu",  # Faute de frappe
        "2"
    ],
    "Test mauvais choix et faute de frappe"
)

# 9. Numéro de téléphone trop court
simulate(
    "whatsapp:+221700000007",
    [
        "bonjour",
        "1",
        "Point E",
        "Yoff",
        "Documents",
        "Moussa",
        "123",  # Numéro trop court
        "789145867",
        "oui"
    ],
    "Test numéro trop court"
)

# 10. Message vide ou incompréhensible
simulate(
    "whatsapp:+221700000008",
    [
        "",  # Message vide
        "bonjour",
        "1",
        "",  # Adresse vide
        "Point E",
        "Yoff",
        "Documents",
        "Moussa",
        "789145867",
        "oui"
    ],
    "Test message vide et champ vide"
)
# Ajoute ce bloc à la fin de test_bot.py
simulate(
    "whatsapp:+221784448524",
    [
        "bonjour",
        "1",
        "Point E",
        "Yoff",
        "Documents",
        "Moussa",
        "789145867",
        "oui"
    ],
    "Test PDF avec logo"
)