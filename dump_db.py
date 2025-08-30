import os
import subprocess
import datetime
import getpass # Pour masquer le mot de passe à la saisie

def dump_mysql_database():
    """
    Demande les informations de connexion MySQL et crée un dump de la base de données.
    """
    print("--- Création d'un dump de base de données MySQL avec Python ---")
    print("")

    # --- Configuration du chemin mysqldump ---
    # Pour MAMP PRO sur macOS
    # Adapte ce chemin si ton installation MAMP est différente ou ta version de MySQL
    # Tu peux aussi le rendre configurable par l'utilisateur si nécessaire.
    MYSQLDUMP_PATH = "/Applications/MAMP/Library/bin/mysql80/bin/mysqldump"
    # Si tu es sur Windows et que MAMP est installé dans C:\MAMP:
    # MYSQLDUMP_PATH = "C:\\MAMP\\bin\\mysql\\mysqlX.X.X\\bin\\mysqldump.exe"
    # Remplace X.X.X par ta version de MySQL, par exemple mysql5.7.26

    # Vérifie si le chemin mysqldump existe
    if not os.path.exists(MYSQLDUMP_PATH):
        print(f"Erreur : mysqldump n'a pas été trouvé à l'emplacement spécifié : {MYSQLDUMP_PATH}")
        print("Veuillez vérifier et ajuster la variable 'MYSQLDUMP_PATH' dans le script.")
        return

    # --- Demande les informations de connexion ---
    db_user = input("Nom d'utilisateur MySQL (ex: root, user_prod) : ")
    db_password = getpass.getpass("Mot de passe MySQL : ") # Masque la saisie du mot de passe
    db_host = input("Hôte MySQL (ex: localhost, ou l'adresse de ton serveur de production) : ")
     # --- NOUVELLE LIGNE : Demander le port si nécessaire ---
    db_port = input("Port MySQL (laisser vide pour le port par défaut 3306, ou saisir le port OVH) : ")
    db_name = input("Nom de la base de données à sauvegarder : ")

    # --- Définir le nom et le chemin du fichier de sortie ---
    # Le fichier sera enregistré sur le bureau de l'utilisateur
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Pour un chemin multi-plateforme vers le bureau
    output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(output_dir, f"{db_name}_{timestamp}.sql")

    # Crée le répertoire de sortie si inexistant
    os.makedirs(output_dir, exist_ok=True)

    # --- Construire la commande mysqldump ---
    # Utilisation d'une liste pour la commande pour gérer les espaces et la sécurité
    command = [
        MYSQLDUMP_PATH,
        f"-h{db_host}",
        f"-u{db_user}",
        f"-p{db_password}", # Attention : mot de passe en clair dans la commande si affichée
        
    ]
# --- AJOUTER LA CONDITION POUR LE PORT ---
    if db_port: # Si l'utilisateur a renseigné un port
        command.append(f"-P{db_port}") # Ajouter -P<port> à la commande
    command.append(db_name) # Ajouter le nom de la base de données à sauvegarder
    print("")
    print(f"Sauvegarde de la base de données '{db_name}' depuis '{db_host}'...")
    if db_port:
        print(f"Utilisation du port : {db_port}")
    print(f"Fichier de sortie : {output_file}")
    print("")

    # --- Exécuter la commande ---
    try:
        # Popen permet d'exécuter la commande et de capturer la sortie/erreur
        # et d'écrire directement dans le fichier de sortie
        with open(output_file, 'w') as f:
            process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE, text=True)
            # Attend que le processus se termine et capture les erreurs
            stderr_output = process.communicate()[1]

        if process.returncode == 0:
            print("✅ Dump de la base de données créé avec succès !")
            print(f"Le fichier de sauvegarde est disponible ici : {output_file}")
        else:
            print(f"❌ Une erreur s'est produite lors de la création du dump (Code d'erreur : {process.returncode}).")
            print(f"Message d'erreur : {stderr_output.strip()}")
            print("Veuillez vérifier vos identifiants et le chemin de mysqldump.")

    except FileNotFoundError:
        print(f"Erreur : Le programme mysqldump n'a pas été trouvé à l'emplacement : {MYSQLDUMP_PATH}")
        print("Veuillez vous assurer que le chemin est correct et que mysqldump est installé.")
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {e}")

    print("--- Opération terminée ---")

if __name__ == "__main__":
    dump_mysql_database()
    