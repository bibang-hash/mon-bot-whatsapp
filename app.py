import time
import re
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
import qrcode
from io import BytesIO

app = Flask(__name__)

user_states = {}

NGROK_URL = "https://b1af-2001-4278-80-4d61-15f7-aa34-2b74-b981.ngrok-free.app"

quartiers_dakar = [
    "Plateau", "Medina", "Yoff", "Ouakam", "Liberté", "Parcelles", "Hann", "Grand Yoff",
    "Pikine", "Guédiawaye", "Sacré Coeur", "Fann", "Almadies", "Mermoz", "Ngor", "Dieuppeul"
]

PHRASE_PREVENTION = "\n⚠️ Merci d’attendre la réponse du bot avant d’envoyer la prochaine information."

def send_quartiers_list(msg):
    quartiers_page = quartiers_dakar[:10]
    options = "\n".join([f"{i+1}. {q}" for i, q in enumerate(quartiers_page)])
    msg.body(
        f"📍 Choisissez le quartier parmi la liste suivante :\n{options}\n"
        "Répondez par le numéro du quartier ou tapez le nom exact.\n"
        "Ou partagez votre position (📎 > Localisation)."
        + PHRASE_PREVENTION
    )

def save_demande(data, type_livraison):
    file_exists = os.path.isfile("demandes.csv")
    with open("demandes.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["type", "infos"])
        writer.writerow([type_livraison, str(data)])

def generer_bon_pdf(data, type_livraison):
    dossier = "bons_livraison"
    if not os.path.exists(dossier):
        os.makedirs(dossier)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"{dossier}/bon_{type_livraison}_{now}.pdf"
    c = canvas.Canvas(nom_fichier, pagesize=A4)
    largeur, hauteur = A4

    logo_path = "Dsp_logo-1.png"
    logo_width = 120
    logo_height = 120
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            (largeur - logo_width) / 2,
            hauteur - logo_height - 30,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            mask='auto'
        )

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#E6D3B3"))
    c.drawCentredString(largeur / 2, hauteur - logo_height - 50, "Bon de livraison")
    c.setFillColor(colors.black)

    encadre_x = 40
    encadre_y = hauteur - logo_height - 270
    encadre_w = largeur - 80
    encadre_h = 200
    c.setFillColor(colors.HexColor("#F7F3ED"))
    c.roundRect(encadre_x, encadre_y, encadre_w, encadre_h, 10, fill=1, stroke=0)
    c.setFillColor(colors.black)

    c.setStrokeColor(colors.HexColor("#E6D3B3"))
    c.line(encadre_x, encadre_y + encadre_h, encadre_x + encadre_w, encadre_y + encadre_h)
    c.line(encadre_x, encadre_y, encadre_x + encadre_w, encadre_y)
    c.setStrokeColor(colors.black)

    c.setFont("Helvetica", 13)
    y = encadre_y + encadre_h - 25

    labels = {
        "pickup": "Quartier de récupération",
        "pickup_gps": "Géolocalisation récupération",
        "delivery": "Quartier de livraison",
        "delivery_gps": "Géolocalisation livraison",
        "description": "Description du colis",
        "recipient_name": "Nom du destinataire",
        "recipient_phone": "Téléphone du destinataire",
        "restaurant_name": "Nom du restaurant",
        "restaurant_address": "Adresse du restaurant",
        "restaurant_gps": "Géolocalisation restaurant",
        "client_name": "Nom du client",
        "client_address": "Adresse du client",
        "client_gps": "Géolocalisation client",
        "client_phone": "Téléphone du client",
        "order_number": "Numéro de commande",
        "depart": "Quartier de départ",
        "depart_gps": "Géolocalisation départ",
        "colis_type": "Type/Nombre de colis",
        "pickup_time": "Heure de récupération",
        "ref": "Référence interne"
    }

    c.drawString(encadre_x + 15, y, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 22
    c.drawString(encadre_x + 15, y, f"Type : {type_livraison.capitalize()}")
    y -= 22

    qr_drawn = False
    for k, v in data.items():
        label = labels.get(k, k.replace('_', ' ').capitalize())
        if k.endswith("_gps") and v:
            c.drawString(encadre_x + 15, y, f"{label} : {v}")
            y -= 18
            c.setFillColor(colors.HexColor("#0074D9"))
            maps_url = f"https://maps.google.com/?q={v}"
            c.drawString(encadre_x + 25, y, maps_url)
            c.setFillColor(colors.black)
            if not qr_drawn:
                qr = qrcode.make(maps_url)
                qr_buffer = BytesIO()
                qr.save(qr_buffer)
                qr_buffer.seek(0)
                qr_img = ImageReader(qr_buffer)
                c.drawImage(qr_img, encadre_x + encadre_w - 90, encadre_y + encadre_h - 90, width=70, height=70)
                qr_drawn = True
            y -= 22
        else:
            c.drawString(encadre_x + 15, y, f"{label} : {v}")
            y -= 22

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor("#E6D3B3"))
    c.drawCentredString(largeur / 2, 35, "Dakar Speed Pro – 78 444 85 24 – Livraison rapide et fiable à Dakar")
    c.setFillColor(colors.black)

    c.save()
    return nom_fichier

def get_gps_from_request(prefix):
    lat = request.values.get(f"{prefix}Latitude")
    lng = request.values.get(f"{prefix}Longitude")
    if lat and lng:
        return f"{lat},{lng}"
    return None

def is_valid_phone(phone):
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) == 9 and digits.startswith(("77", "78", "76", "70", "33"))

def format_phone(phone):
    digits = ''.join(filter(str.isdigit, phone))
    return f"{digits[:2]} {digits[2:5]} {digits[5:]}" if len(digits) == 9 else phone

def is_valid_name(name):
    return bool(re.match(r"^[A-Za-zÀ-ÿ' -]{2,}$", name.strip()))

def is_valid_description(desc):
    return len(desc.strip()) >= 3 and re.search(r"[A-Za-z]", desc)

def is_valid_time(timestr):
    match = re.match(r"^\s*(\d{1,2})\s*[hH:]\s*(\d{2})\s*$", timestr)
    if not match:
        return False
    h, m = int(match.group(1)), int(match.group(2))
    return 0 <= h <= 23 and 0 <= m <= 59

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    user_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    now = time.time()
    if user_number in user_states:
        last_reply = user_states[user_number].get("last_reply_time", 0)
        if now - last_reply < 1:
            return ""

    menu_classique = ["1", "classique"]
    menu_repas = ["2", "repas"]
    menu_entreprise = ["3", "entreprise"]

    if incoming_msg_lower == "annuler":
        user_states[user_number] = {"step": 0, "type": None, "data": {}, "last_reply_time": time.time()}
        msg.body("❌ Votre demande a été annulée. Tapez 'bonjour' pour recommencer.\n🚀 *Dakar Speed Pro reste à votre service !*" + PHRASE_PREVENTION)
        return str(resp)

    if incoming_msg_lower == "retour":
        user_states[user_number] = {"step": 0, "type": None, "data": {}, "last_reply_time": time.time()}
        msg.body(
            "🔙 Retour au menu principal.\n"
            "Bienvenue chez Dakar Speed Pro !\n"
            "Quel type de livraison souhaitez-vous ?\n"
            "1️⃣ Classique\n"
            "2️⃣ Repas\n"
            "3️⃣ Entreprise\n"
            "Répondez par 1, 2 ou 3.\n"
            "Exemple : tapez 1 pour Classique."
            + PHRASE_PREVENTION
        )
        return str(resp)

    if incoming_msg_lower in ["aide", "agent", "support"]:
        user_states[user_number]["last_reply_time"] = time.time()
        msg.body("🧑‍💼 Un agent va vous répondre sous peu. Merci de patienter ou appelez le 78 444 85 24.\nℹ️ *Dakar Speed Pro* – Livraison rapide et fiable à Dakar." + PHRASE_PREVENTION)
        return str(resp)

    if incoming_msg_lower.startswith("suivi"):
        recherche = incoming_msg_lower.replace("suivi", "").strip()
        if not recherche:
            user_states[user_number]["last_reply_time"] = time.time()
            msg.body("🔎 Merci d'indiquer le numéro de téléphone ou la référence à suivre. Exemple : suivi 77 123 45 67" + PHRASE_PREVENTION)
            return str(resp)
        trouve = False
        if os.path.isfile("demandes.csv"):
            with open("demandes.csv", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if recherche in row[1].lower():
                        user_states[user_number]["last_reply_time"] = time.time()
                        msg.body(f"✅ Demande trouvée :\nType : {row[0]}\nInfos : {row[1]}" + PHRASE_PREVENTION)
                        trouve = True
                        break
        if not trouve:
            user_states[user_number]["last_reply_time"] = time.time()
            msg.body("❗Aucune demande trouvée avec cette information.\nℹ️ *Dakar Speed Pro* – Livraison rapide et fiable à Dakar." + PHRASE_PREVENTION)
        return str(resp)

    if user_number not in user_states:
        user_states[user_number] = {"step": 0, "type": None, "data": {}, "last_reply_time": 0}

    state = user_states[user_number]
    print(f"[{user_number}] Step: {state.get('step')} | Type: {state.get('type')} | Msg: {incoming_msg}")

    if incoming_msg_lower in ["bonjour", "menu", "recommencer"]:
        user_states[user_number] = {"step": 0, "type": None, "data": {}, "last_reply_time": time.time()}
        state = user_states[user_number]
        msg.body(
            "👋 Bienvenue chez Dakar Speed Pro !\n"
            "Quel type de livraison souhaitez-vous ?\n"
            "1️⃣ Classique\n"
            "2️⃣ Repas\n"
            "3️⃣ Entreprise\n"
            "Répondez par 1, 2 ou 3.\n"
            "Exemple : tapez 1 pour Classique."
            + PHRASE_PREVENTION
        )
        state["step"] = 1
        return str(resp)

    # ... (toute la logique métier inchangée) ...

    # Confirmation avant enregistrement final
    if state.get("step") == "confirmation":
        if incoming_msg_lower == "oui":
            save_demande(state["data"], state["type"])
            chemin_pdf = generer_bon_pdf(state["data"], state["type"])
            pdf_url = f"{NGROK_URL}/{chemin_pdf.replace(os.sep, '/')}"
            gps_keys = [k for k in state["data"] if k.endswith("_gps") and state["data"][k]]
            maps_links = ""
            for k in gps_keys:
                maps_links += f"\n🔗 Lien Google Maps : https://maps.google.com/?q={state['data'][k]}"
            msg.body(
                "✅ Votre demande a bien été prise en compte.\n"
                "👉 *Cliquez ici pour ouvrir le bon de livraison PDF :*\n"
                f"{pdf_url}\n"
                f"{maps_links if maps_links else ''}\n"
                "🚀 *Dakar Speed Pro vous remercie et vous souhaite une excellente journée ou soirée !*\n"
                "Pour toute question, contactez-nous au 78 444 85 24."
                + PHRASE_PREVENTION
            )
            user_states[user_number] = {"step": 0, "type": None, "data": {}, "last_reply_time": time.time()}
            return str(resp)
        elif incoming_msg_lower == "non":
            msg.body("❌ Votre demande a été annulée. Tapez 'bonjour' pour recommencer.\n🚀 *Dakar Speed Pro reste à votre service !*" + PHRASE_PREVENTION)
            user_states[user_number] = {"step": 0, "type": None, "data": {}, "last_reply_time": time.time()}
            return str(resp)
        else:
            msg.body(
                "Merci de répondre par 'oui' pour confirmer ou 'non' pour annuler.\nExemple : oui\n"
                "ℹ️ *Dakar Speed Pro* – Livraison rapide et fiable à Dakar."
                + PHRASE_PREVENTION
            )
            user_states[user_number]["last_reply_time"] = time.time()
            return str(resp)

    # Si aucune condition n'est remplie, message explicite d'erreur
    msg.body(
        "❗Je n'ai pas compris votre réponse. Merci de suivre les instructions ou tapez 'retour' pour recommencer.\n"
        "ℹ️ *Dakar Speed Pro* – Livraison rapide et fiable à Dakar."
        + PHRASE_PREVENTION
    )
    user_states[user_number]["last_reply_time"] = time.time()
    return str(resp)

@app.route('/bons_livraison/<filename>')
def serve_pdf(filename):
    from flask import send_from_directory
    return send_from_directory('bons_livraison', filename)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)