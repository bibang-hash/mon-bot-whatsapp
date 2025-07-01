from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
import os

app = Flask(__name__)

user_states = {}

def save_demande(data, type_livraison):
    file_exists = os.path.isfile("demandes.csv")
    with open("demandes.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["type", "infos"])
        writer.writerow([type_livraison, str(data)])

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    user_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    # Gestion fautes de frappe pour le menu principal
    menu_classique = ["1", "classique", "classiqu", "clasique", "clasic"]
    menu_repas = ["2", "repas", "repaz", "repas ", "repaz "]
    menu_entreprise = ["3", "entreprise", "entrepriz", "entrepise", "entreprize"]

    # Annulation à tout moment
    if incoming_msg_lower == "annuler":
        user_states[user_number] = {"step": 0, "type": None, "data": {}}
        msg.body("❌ Votre demande a été annulée. Tapez 'bonjour' pour recommencer.")
        return str(resp)

    # Retour au menu principal à tout moment
    if incoming_msg_lower == "retour":
        user_states[user_number] = {"step": 0, "type": None, "data": {}}
        msg.body(
            "🔙 Retour au menu principal.\n"
            "Bienvenue chez Dakar Speed Pro !\n"
            "Quel type de livraison souhaitez-vous ?\n"
            "1️⃣ Classique\n"
            "2️⃣ Repas\n"
            "3️⃣ Entreprise\n"
            "Répondez par 1, 2 ou 3."
        )
        return str(resp)

    # Support client à tout moment
    if incoming_msg_lower in ["aide", "agent", "support"]:
        msg.body("🧑‍💼 Un agent va vous répondre sous peu. Merci de patienter ou appelez le 78 444 85 24.")
        return str(resp)

    # Suivi de livraison
    if incoming_msg_lower.startswith("suivi"):
        recherche = incoming_msg_lower.replace("suivi", "").strip()
        if not recherche:
            msg.body("🔎 Merci d'indiquer le numéro de téléphone ou la référence à suivre. Exemple : suivi 78 914 58 67")
            return str(resp)
        trouve = False
        if os.path.isfile("demandes.csv"):
            with open("demandes.csv", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)  # skip header
                for row in reader:
                    if recherche in row[1].lower():
                        msg.body(f"✅ Demande trouvée :\nType : {row[0]}\nInfos : {row[1]}")
                        trouve = True
                        break
        if not trouve:
            msg.body("❗Aucune demande trouvée avec cette information.")
        return str(resp)

    if user_number not in user_states:
        user_states[user_number] = {"step": 0, "type": None, "data": {}}

    state = user_states[user_number]
    print(f"[{user_number}] Step: {state.get('step')} | Type: {state.get('type')} | Msg: {incoming_msg}")

    # Permettre de relancer le menu à tout moment et afficher le menu immédiatement
    if incoming_msg_lower in ["bonjour", "menu", "recommencer"]:
        user_states[user_number] = {"step": 0, "type": None, "data": {}}
        state = user_states[user_number]
        msg.body(
            "👋 Bienvenue chez Dakar Speed Pro !\n"
            "Quel type de livraison souhaitez-vous ?\n"
            "1️⃣ Classique\n"
            "2️⃣ Repas\n"
            "3️⃣ Entreprise\n"
            "Répondez par 1, 2 ou 3."
        )
        state["step"] = 1
        return str(resp)

    # Confirmation avant enregistrement final
    if state.get("step") == "confirmation":
        if incoming_msg_lower == "oui":
            save_demande(state["data"], state["type"])
            msg.body("✅ Votre demande a bien été prise en compte. Merci !")
            user_states[user_number] = {"step": 0, "type": None, "data": {}}
        elif incoming_msg_lower == "non":
            msg.body("❌ Votre demande a été annulée. Tapez 'bonjour' pour recommencer.")
            user_states[user_number] = {"step": 0, "type": None, "data": {}}
        else:
            msg.body("Merci de répondre par 'oui' pour confirmer ou 'non' pour annuler.")
        return str(resp)

    # Menu principal
    if state["step"] == 0:
        msg.body(
            "👋 Bienvenue chez Dakar Speed Pro !\n"
            "Quel type de livraison souhaitez-vous ?\n"
            "1️⃣ Classique\n"
            "2️⃣ Repas\n"
            "3️⃣ Entreprise\n"
            "Répondez par 1, 2 ou 3."
        )
        state["step"] = 1

    # Choix du type de livraison avec gestion d'erreur et fautes de frappe
    elif state["step"] == 1:
        if incoming_msg_lower in menu_classique:
            state["type"] = "classique"
            msg.body("🚚 Vous avez choisi une livraison classique.\nQuelle est l'adresse de récupération du colis ?")
            state["step"] = 10
        elif incoming_msg_lower in menu_repas:
            state["type"] = "repas"
            msg.body("🍽️ Vous avez choisi une livraison de repas.\nQuel est le nom du restaurant ?")
            state["step"] = 20
        elif incoming_msg_lower in menu_entreprise:
            state["type"] = "entreprise"
            msg.body("🏢 Vous avez choisi une livraison entreprise.\nQuelle est l'adresse de départ ?")
            state["step"] = 30
        else:
            msg.body(
                "❗Je n'ai pas compris votre choix.\n"
                "Merci de répondre par 1️⃣ (Classique), 2️⃣ (Repas) ou 3️⃣ (Entreprise).\n"
                "Tapez 'retour' pour revenir au menu principal."
            )

    # Livraison classique
    elif state["type"] == "classique":
        if state["step"] == 10:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci d'indiquer une adresse de récupération valide.")
            else:
                state["data"]["pickup"] = incoming_msg
                msg.body("Merci. Quelle est l'adresse de livraison ?")
                state["step"] = 11
        elif state["step"] == 11:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci d'indiquer une adresse de livraison valide.")
            else:
                state["data"]["delivery"] = incoming_msg
                msg.body("Merci. Peux-tu décrire le colis à livrer ?")
                state["step"] = 12
        elif state["step"] == 12:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci de donner une description du colis.")
            else:
                state["data"]["description"] = incoming_msg
                msg.body("Merci. Quel est le nom du destinataire ?")
                state["step"] = 13
        elif state["step"] == 13:
            if not incoming_msg or len(incoming_msg) < 2:
                msg.body("❗Merci d'indiquer un nom de destinataire valide.")
            else:
                state["data"]["recipient_name"] = incoming_msg
                msg.body("Merci. Quel est le numéro de téléphone du destinataire ?")
                state["step"] = 14
        elif state["step"] == 14:
            digits = ''.join(filter(str.isdigit, incoming_msg))
            if len(digits) < 9:
                msg.body("❗Merci d'entrer un numéro de téléphone valide (au moins 9 chiffres).")
            else:
                state["data"]["recipient_phone"] = incoming_msg
                recap = (
                    f"📝 Récapitulatif de votre demande :\n"
                    f"- Adresse de récupération : {state['data']['pickup']}\n"
                    f"- Adresse de livraison : {state['data']['delivery']}\n"
                    f"- Description du colis : {state['data']['description']}\n"
                    f"- Destinataire : {state['data']['recipient_name']} ({state['data']['recipient_phone']})\n"
                    "Répondez 'oui' pour confirmer ou 'non' pour annuler."
                )
                msg.body(recap)
                state["step"] = "confirmation"

    # Livraison de repas
    elif state["type"] == "repas":
        if state["step"] == 20:
            if not incoming_msg or len(incoming_msg) < 2:
                msg.body("❗Merci d'indiquer le nom du restaurant.")
            else:
                state["data"]["restaurant_name"] = incoming_msg
                msg.body("Merci. Quelle est l'adresse du restaurant ?")
                state["step"] = 21
        elif state["step"] == 21:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci d'indiquer une adresse de restaurant valide.")
            else:
                state["data"]["restaurant_address"] = incoming_msg
                msg.body("Merci. Quel est le nom du client à livrer ?")
                state["step"] = 22
        elif state["step"] == 22:
            if not incoming_msg or len(incoming_msg) < 2:
                msg.body("❗Merci d'indiquer le nom du client.")
            else:
                state["data"]["client_name"] = incoming_msg
                msg.body("Merci. Quelle est l'adresse de livraison du client ?")
                state["step"] = 23
        elif state["step"] == 23:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci d'indiquer une adresse de livraison valide.")
            else:
                state["data"]["client_address"] = incoming_msg
                msg.body("Merci. Quel est le numéro de téléphone du client ?")
                state["step"] = 24
        elif state["step"] == 24:
            digits = ''.join(filter(str.isdigit, incoming_msg))
            if len(digits) < 9:
                msg.body("❗Merci d'entrer un numéro de téléphone valide (au moins 9 chiffres).")
            else:
                state["data"]["client_phone"] = incoming_msg
                msg.body("Merci. As-tu un numéro de commande ? (Sinon, réponds 'non')")
                state["step"] = 25
        elif state["step"] == 25:
            state["data"]["order_number"] = incoming_msg if incoming_msg.lower() != "non" else "Non communiqué"
            recap = (
                f"📝 Récapitulatif de votre livraison repas :\n"
                f"- Restaurant : {state['data']['restaurant_name']} ({state['data']['restaurant_address']})\n"
                f"- Client : {state['data']['client_name']} ({state['data']['client_address']})\n"
                f"- Téléphone client : {state['data']['client_phone']}\n"
                f"- Numéro de commande : {state['data']['order_number']}\n"
                "Répondez 'oui' pour confirmer ou 'non' pour annuler."
            )
            msg.body(recap)
            state["step"] = "confirmation"

    # Livraison entreprise
    elif state["type"] == "entreprise":
        if state["step"] == 30:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci d'indiquer une adresse de départ valide.")
            else:
                state["data"]["depart"] = incoming_msg
                msg.body("Merci. Quelle est l'adresse de livraison ?")
                state["step"] = 31
        elif state["step"] == 31:
            if not incoming_msg or len(incoming_msg) < 3:
                msg.body("❗Merci d'indiquer une adresse de livraison valide.")
            else:
                state["data"]["delivery"] = incoming_msg
                msg.body("Merci. Quel est le type de colis et le nombre ?")
                state["step"] = 32
        elif state["step"] == 32:
            if not incoming_msg or len(incoming_msg) < 2:
                msg.body("❗Merci d'indiquer le type et le nombre de colis.")
            else:
                state["data"]["colis_type"] = incoming_msg
                msg.body("Merci. À quelle heure doit-on récupérer le colis ?")
                state["step"] = 33
        elif state["step"] == 33:
            if not incoming_msg or len(incoming_msg) < 2:
                msg.body("❗Merci d'indiquer une heure de récupération valide.")
            else:
                state["data"]["pickup_time"] = incoming_msg
                msg.body("Merci. Quel est le numéro de téléphone du destinataire ?")
                state["step"] = 34
        elif state["step"] == 34:
            digits = ''.join(filter(str.isdigit, incoming_msg))
            if len(digits) < 9:
                msg.body("❗Merci d'entrer un numéro de téléphone valide (au moins 9 chiffres).")
            else:
                state["data"]["recipient_phone"] = incoming_msg
                msg.body("Merci. As-tu une référence interne ? (Sinon, réponds 'non')")
                state["step"] = 35
        elif state["step"] == 35:
            state["data"]["ref"] = incoming_msg if incoming_msg.lower() != "non" else "Non communiqué"
            recap = (
                f"📝 Récapitulatif de votre livraison entreprise :\n"
                f"- Adresse de départ : {state['data']['depart']}\n"
                f"- Adresse de livraison : {state['data']['delivery']}\n"
                f"- Type/Nombre de colis : {state['data']['colis_type']}\n"
                f"- Heure de récupération : {state['data']['pickup_time']}\n"
                f"- Téléphone destinataire : {state['data']['recipient_phone']}\n"
                f"- Référence interne : {state['data']['ref']}\n"
                "Facturation mensuelle possible.\n"
                "Répondez 'oui' pour confirmer ou 'non' pour annuler."
            )
            msg.body(recap)
            state["step"] = "confirmation"

    else:
        msg.body("Merci pour votre message. Un agent va vous répondre bientôt.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)