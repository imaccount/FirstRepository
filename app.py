import requests

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def get_intent_from_text(text):
    intents_with_repo = ['list_repo_contributors', 'list_repo_commits', 'get_number_of_commits', 'delete_repo', 'list_branches', 'create_branch', 'repository_report', 'list_repo_languages','search_in_code']
    intents_with_new_repo = ['create_repo']
    intents_with_2_args = ['create_branch', 'search_in_code']
    rasa_ip = 'localhost'
    rasa_url = f"http://{rasa_ip}:5005/model/parse"  # URL de l'API de Rasa
    payload = {"text": text}

    try :
        response = requests.post(rasa_url, json=payload)
        if response.status_code == 200:
            intent = response.json().get("intent", {}).get("name")
            confidence = response.json().get("intent", {}).get("confidence")
            print(f"Intent détecté : {intent} (confiance : {confidence})")

            # print(f"response : {response.json()}")
            if confidence > 0.7 : 
                function_to_call = intent_functions.get(intent)
            elif confidence > 0.3 :
                function_to_call = intent_functions.get('not_sure_of_the_intent')
            else : 
                function_to_call = intent_functions.get('intent_not_understood')


            try:
                repo = extract_entities(response.json()).get('repo')
                if intent in intents_with_repo:
                    repo = get_repo_from_query(repo, user_repos)
                    print(f"Repo détecté : {repo}")
            except Exception as e:
                print("Aucun repo ni orga détecté.")
                repo = None
            mapped_repo = {"repo": repo} if repo else {}

            try:
                arg2 = extract_entities(response.json()).get('branch')
            except Exception as e:
                print("Aucune branche détectée.")
                arg2 = None

            #Pas de branche, donc on cherche un keyword
            if arg2 is None:
                try:
                    arg2 = extract_entities(response.json()).get('keyword')
                except Exception as e:
                    print("Aucun mot-clé détecté.")
                    arg2 = None

            # Appeler la fonction si elle existe
            if function_to_call:
                if function_to_call == not_sure_of_the_intent :
                    repo = mapped_repo['repo'] or ''
                    result = function_to_call(intent, repo)
                elif (intent in intents_with_repo or intent in intents_with_new_repo) and intent not in intents_with_2_args:
                    if mapped_repo == {} :
                        result = intent_functions.get('intent_not_understood')()
                    else : 
                        result = function_to_call(mapped_repo['repo'])
                elif intent in intents_with_2_args:
                    if mapped_repo == {} or arg2 == None:
                        result = intent_functions.get('intent_not_understood')()
                    else : 
                        result = function_to_call(mapped_repo['repo'], arg2)
                elif function_to_call == subscribe_repo :
                    if mapped_repo == {} :
                        result = intent_functions.get('intent_not_understood')()
                    else :
                        result = function_to_call(mapped_repo['repo'])
                else:
                    result = function_to_call()

                tts = gTTS(text=result, lang='fr')

                # Sauvegarder le fichier audio
                
                tts.save("message.mp3")
                # Initialiser pygame mixer
                pygame.mixer.init()

                # Charger et jouer le fichier audio
                try :
                    pygame.mixer.music.load("message.mp3")
                    pygame.mixer.music.play()
                except Exception as e :
                    print(f"Could not read the message : {e}")
            else:
                result = intent_functions.get('intent_not_understood')
            return intent
        else:
            print("Erreur lors de la connexion à l'API Rasa")
            return None
    except Exception as e :
        print(e)


# Définissez une route pour écouter sur le port 5000 et récupérer le texte envoyé via POST
@app.route('/receive_text', methods=['POST'])
def receive_texte():
    # Récupérer le contenu JSON de la requête
    data = request.get_json()

    # Vérifier si le texte est bien présent dans la requête
    if not data or 'text' not in data:
        return jsonify({"error": "Aucun texte trouvé dans la requête"}), 400

    # Récupérer le texte
    texte_recu = data['text']
    print(f"Texte reçu : {texte_recu}")

    get_intent_from_text(texte_recu)

    return jsonify({"message": "Texte reçu avec succès", "text": texte_recu}), 200

@app.route('/scxml_event', methods=['POST'])
def receive_texte2():
    # Récupérer le contenu JSON de la requête
    data = request.get_json()

    # Vérifier si le texte est bien présent dans la requête
    if not data or 'text' not in data:
        return jsonify({"error": "Aucun texte trouvé dans la requête"}), 400

    # Récupérer le texte
    texte_recu = data['text']
    print(f"Texte reçu : {texte_recu}")

    return jsonify({"message": "Texte reçu avec succès", "text": texte_recu}), 200

if __name__ == '__main__':
    # Lancer le serveur sur le port 5000
    app.run(port=5000, debug=True)