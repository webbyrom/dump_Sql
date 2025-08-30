import tkinter as tk
from tkinter import messagebox, filedialog
import os
import subprocess
import datetime
import sys
import shutil
import threading
import zipfile
import json # Pour la persistance des préférences

# --- Chemin du fichier de préférences ---
PREFS_FILE = "mysqldumper_prefs.json"

# --- Fonction utilitaire pour les chemins des ressources (pour PyInstaller) ---
def resource_path(relative_path):
    """
    Obtient le chemin absolu d'une ressource, fonctionne en développement
    et après la compilation avec PyInstaller.
    """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En mode développement, le chemin de base est le répertoire du script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- Fonctions utilitaires pour la détection de mysqldump ---
def find_mysqldump():
    """
    Tente de trouver le chemin de l'exécutable mysqldump sur le système.
    Vérifie le PATH système, puis les emplacements communs de MAMP/XAMPP.
    """
    # 1. Vérifier le PATH système en premier
    mysqldump_exe = shutil.which("mysqldump")
    if mysqldump_exe:
        return mysqldump_exe

    # 2. Vérifier les chemins communs de MAMP/XAMPP (macOS)
    if sys.platform == 'darwin':  # macOS
        # Chemins MAMP PRO (peut varier selon les versions de MySQL)
        mamp_pro_paths = [
            "/Applications/MAMP/Library/bin/mysql/bin/mysqldump", # Ancien chemin MAMP
            "/Applications/MAMP/Library/bin/mysql80/bin/mysqldump", # MAMP Pro MySQL 8
            "/Applications/MAMP/Library/bin/mysql57/bin/mysqldump", # MAMP Pro MySQL 5.7
            # Ajouter d'autres chemins si nécessaire pour différentes versions MySQL de MAMP
        ]
        for path in mamp_pro_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

    # 3. Vérifier les chemins communs de MAMP/XAMPP (Windows)
    elif sys.platform.startswith('win'):  # Windows
        xampp_path = os.path.join(os.environ.get('XAMPP_HOME', 'C:\\xampp'), 'mysql', 'bin', 'mysqldump.exe')
        if os.path.exists(xampp_path) and os.access(xampp_path, os.X_OK):
            return xampp_path

        mamp_win_base = os.path.join('C:\\MAMP', 'bin', 'mysql')
        if os.path.exists(mamp_win_base):
            # Chercher les versions spécifiques (e.g., mysql5.7.X, mysql8.0.X)
            for version_dir in os.listdir(mamp_win_base):
                if version_dir.startswith('mysql'):
                    specific_path_win = os.path.join(mamp_win_base, version_dir, 'bin', 'mysqldump.exe')
                    if os.path.exists(specific_path_win) and os.access(specific_path_win, os.X_OK):
                        return specific_path_win

    return "" # Retourne une chaîne vide si mysqldump n'est pas trouvé

def browse_mysqldump_path():
    """Ouvre une boîte de dialogue pour sélectionner l'exécutable mysqldump."""
    file_selected = filedialog.askopenfilename(
        title="Sélectionner l'exécutable mysqldump",
        filetypes=[("Exécutables", "mysqldump*"), ("Tous les fichiers", "*.*")]
    )
    if file_selected:
        mysqldump_path_var.set(file_selected)
        save_preferences() # Sauvegarde la préférence immédiatement

def select_output_folder():
    """Ouvre une boîte de dialogue pour sélectionner le dossier de sortie."""
    folder_selected = filedialog.askdirectory(
        title="Sélectionner le dossier de sortie"
    )
    if folder_selected:
        output_folder_path.set(folder_selected)
        output_folder_label.config(text=f"Dossier de sortie : {folder_selected}")
        save_preferences() # Sauvegarde la préférence immédiatement

def run_dump_in_thread():
    """Lance la fonction de dump dans un thread séparé pour ne pas bloquer l'interface."""
    # Désactive le bouton pour éviter les lancements multiples
    dump_button.config(state=tk.DISABLED)
    open_folder_button.config(state=tk.DISABLED) # Désactive le bouton d'ouverture de dossier
    status_label.config(text="Démarrage du dump (peut prendre quelques instants)...", fg="orange")
    window.update_idletasks()

    # Sauvegarde les préférences (sans le mot de passe) avant de lancer le dump
    save_preferences()

    # Lance le dump dans un thread séparé
    dump_thread = threading.Thread(target=dump_mysql_database_gui_logic)
    dump_thread.start()

def dump_mysql_database_gui_logic():
    """
    Récupère les informations de l'interface graphique et exécute la commande mysqldump localement.
    """
    global last_output_folder # Déclaration globale unique au début de la fonction

    db_user = user_entry.get()
    db_password = password_entry.get() # Récupère le mot de passe directement depuis le champ (non sauvegardé)
    db_host = host_entry.get()
    db_port_str = port_entry.get() # Récupère la chaîne du port
    db_name = name_entry.get()
    mysqldump_exe_path = mysqldump_path_var.get()
    output_folder = output_folder_path.get()

    # --- Validations ---
    if not db_user or not db_host or not db_name:
        messagebox.showwarning("Champs manquants", "Veuillez remplir au moins l'utilisateur, l'hôte et le nom de la base de données.")
        reset_ui_after_completion()
        return

    # Validation du port
    db_port = None
    if db_port_str:
        try:
            db_port = int(db_port_str)
        except ValueError:
            messagebox.showwarning("Port invalide", "Le port doit être un nombre entier valide.")
            reset_ui_after_completion()
            return

    if not output_folder or not os.path.isdir(output_folder):
        messagebox.showwarning("Dossier de sortie invalide", "Veuillez sélectionner un dossier de sortie valide.")
        reset_ui_after_completion()
        return

    if not mysqldump_exe_path or not os.path.exists(mysqldump_exe_path) or not os.access(mysqldump_exe_path, os.X_OK):
        messagebox.showerror("Erreur de configuration",
                             "Le chemin de mysqldump est invalide ou l'exécutable n'existe pas ou n'est pas exécutable.\n"
                             "Veuillez le renseigner manuellement ou vérifier l'installation.")
        reset_ui_after_completion()
        return
    
    # --- Définir le nom du fichier de sortie ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_base = f"{db_name}_{timestamp}"
    output_sql_file = os.path.join(output_folder, f"{output_file_base}.sql")
    zip_file = os.path.join(output_folder, f"{output_file_base}.zip")

    # --- Construire la commande mysqldump ---
    command = [
        mysqldump_exe_path,
        f"-h{db_host}",
        f"-u{db_user}",
        f"-p{db_password}", # Mot de passe directement dans la commande (non sauvegardé)
        db_name,
        "--single-transaction",
        "--routines",
        "--triggers",
        "--events",
        "--add-drop-database",
        "--add-drop-table",
        "--default-character-set=utf8mb4",
        "--set-gtid-purged=OFF"
    ]

    if db_port: # Ajouter le port si renseigné
        command.insert(2, f"-P{db_port}") # Insérer après -u et avant -p pour une meilleure convention

    status_label.config(text=f"Sauvegarde en cours de '{db_name}' vers '{output_sql_file}'...", fg="orange")
    window.update_idletasks()

    # --- Exécuter la commande ---
    try:
        with open(output_sql_file, 'w', encoding='utf-8') as f: # Spécifier l'encodage pour le fichier de sortie
            process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stderr_output = process.communicate()[1]

        if process.returncode == 0:
            # --- Compression ZIP ---
            status_label.config(text=f"Dump terminé. Compression en cours vers '{zip_file}'...", fg="orange")
            window.update_idletasks()
            try:
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(output_sql_file, os.path.basename(output_sql_file))
                os.remove(output_sql_file) # Supprime le fichier SQL non compressé
                messagebox.showinfo("Succès", f"Dump créé et compressé avec succès !\nFichier : {zip_file}")
                status_label.config(text=f"Dump et compression réussis. Fichier : {os.path.basename(zip_file)}", fg="green")
                open_folder_button.config(state=tk.NORMAL) # Active le bouton d'ouverture de dossier
                last_output_folder = output_folder # Stocke le dernier dossier de sortie
            except Exception as zip_err:
                messagebox.showwarning("Avertissement", f"Dump créé, mais erreur lors de la compression ZIP : {zip_err}\n"
                                                      f"Le fichier SQL non compressé est disponible ici : {output_sql_file}")
                status_label.config(text="Dump réussi, compression échouée.", fg="orange")
                open_folder_button.config(state=tk.NORMAL)
                last_output_folder = output_folder
        else:
            error_message = f"Une erreur s'est produite lors du dump (Code : {process.returncode}).\n"
            error_message += f"Message de mysqldump : {stderr_output.strip()}" if stderr_output.strip() else "Aucun message d'erreur détaillé de mysqldump."
            messagebox.showerror("Erreur", error_message)
            status_label.config(text="Erreur lors du dump.", fg="red")

    except FileNotFoundError:
        messagebox.showerror("Erreur", f"Le programme mysqldump n'a pas été trouvé à l'emplacement : {mysqldump_exe_path}\n"
                                       "Vérifiez que le chemin est correct.")
        status_label.config(text="Erreur : mysqldump introuvable.", fg="red")
    except Exception as e:
        messagebox.showerror("Erreur inattendue", f"Une erreur inattendue s'est produite : {e}")
        status_label.config(text="Erreur inattendue.", fg="red")
    finally:
        reset_ui_after_completion()

def reset_ui_after_completion():
    """Réactive le bouton de dump et réinitialise le statut."""
    dump_button.config(state=tk.NORMAL)
    # Le bouton open_folder_button est géré dans la section de succès/échec du dump
    if status_label.cget("fg") not in ["green", "orange", "red"]: # Ne pas écraser les messages de succès/échec
        status_label.config(text="Prêt.", fg="blue")

def open_last_output_folder():
    """Ouvre le dernier dossier de sortie dans l'explorateur de fichiers du système."""
    if last_output_folder and os.path.isdir(last_output_folder):
        try:
            if sys.platform == "win32":
                os.startfile(last_output_folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", last_output_folder])
            else: # Linux
                subprocess.Popen(["xdg-open", last_output_folder])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier : {e}")
    else:
        messagebox.showwarning("Dossier introuvable", "Aucun dossier de sortie valide n'a été enregistré.")

# --- Fonctions de persistance des préférences ---
def save_preferences():
    """Sauvegarde les préférences de l'utilisateur dans un fichier JSON (sans le mot de passe)."""
    prefs = {
        "db_user": user_entry.get(),
        # "db_password": password_entry.get(), # Le mot de passe n'est plus sauvegardé pour des raisons de sécurité
        "db_host": host_entry.get(),
        "db_port": port_entry.get(),
        "db_name": name_entry.get(),
        "mysqldump_path": mysqldump_path_var.get(),
        "output_folder": output_folder_path.get()
    }
    try:
        with open(PREFS_FILE, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des préférences : {e}")

def load_preferences():
    """Charge les préférences de l'utilisateur depuis un fichier JSON (sans le mot de passe)."""
    try:
        with open(PREFS_FILE, 'r') as f:
            prefs = json.load(f)
            user_entry.insert(0, prefs.get("db_user", "root"))
            # password_entry.insert(0, prefs.get("db_password", "root")) # Le mot de passe n'est plus chargé
            host_entry.insert(0, prefs.get("db_host", "localhost"))
            port_entry.insert(0, prefs.get("db_port", ""))
            name_entry.insert(0, prefs.get("db_name", ""))
            mysqldump_path_var.set(prefs.get("mysqldump_path", find_mysqldump()))
            
            default_output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            output_folder_path.set(prefs.get("output_folder", default_output_dir))
            output_folder_label.config(text=f"Dossier de sortie : {output_folder_path.get()}")
            
    except FileNotFoundError:
        # Si le fichier n'existe pas, initialiser avec les valeurs par défaut
        user_entry.insert(0, "root")
        password_entry.insert(0, "") # Le mot de passe est vide par défaut
        host_entry.insert(0, "localhost")
        port_entry.insert(0, "")
        name_entry.insert(0, "")
        mysqldump_path_var.set(find_mysqldump())
        default_output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        output_folder_path.set(default_output_dir)
        output_folder_label.config(text=f"Dossier de sortie : {output_folder_path.get()}")
    except Exception as e:
        print(f"Erreur lors du chargement des préférences : {e}")
        # En cas d'erreur de chargement, s'assurer que les champs sont quand même initialisés
        user_entry.insert(0, "root")
        password_entry.insert(0, "") # Le mot de passe est vide par défaut
        host_entry.insert(0, "localhost")
        port_entry.insert(0, "")
        name_entry.insert(0, "")
        mysqldump_path_var.set(find_mysqldump())
        default_output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        output_folder_path.set(default_output_dir)
        output_folder_label.config(text=f"Dossier de sortie : {output_folder_path.get()}")


# --- Configuration de l'interface Tkinter ---
window = tk.Tk()
window.title("MySQL Database Dumper Local")
window.geometry("650x580") # Taille initiale de la fenêtre, légèrement ajustée
window.resizable(False, False) # Empêche le redimensionnement de la fenêtre

# --- Définir l'icône de l'application ---
# Placez votre fichier d'icône (par exemple, 'app_icon.png') dans le même dossier que votre script Python.
# Pour Windows, un fichier .ico est souvent préféré. Pour macOS/Linux, .png est courant.
# Si l'icône n'est pas trouvée, l'application fonctionnera toujours sans icône personnalisée.
try:
    # Pour les icônes PNG (généralement pour macOS/Linux)
    icon_path_png = resource_path("app_icon.png")
    if os.path.exists(icon_path_png):
        photo = tk.PhotoImage(file=icon_path_png)
        window.iconphoto(False, photo) # False pour ne pas propager aux sous-fenêtres par défaut

    # Pour les icônes ICO (généralement pour Windows)
    # Note: Tkinter peut avoir des limitations avec les fichiers .ico sur certains OS,
    # mais il est bon de le tenter si vous ciblez Windows.
    icon_path_ico = resource_path("app_icon.ico")
    if os.path.exists(icon_path_ico):
        window.iconbitmap(icon_path_ico)
except Exception as e:
    print(f"Attention: Impossible de charger l'icône de l'application. Erreur: {e}")


# Cadre principal pour un meilleur alignement
main_frame = tk.Frame(window, padx=20, pady=20)
main_frame.pack(expand=True, fill="both")

# Variables Tkinter
user_entry = tk.Entry(main_frame, width=40)
password_entry = tk.Entry(main_frame, width=40, show="*")
host_entry = tk.Entry(main_frame, width=40)
port_entry = tk.Entry(main_frame, width=40)
name_entry = tk.Entry(main_frame, width=40)

mysqldump_path_var = tk.StringVar()
output_folder_path = tk.StringVar()

# Variable globale pour stocker le dernier dossier de sortie
last_output_folder = None

# Labels et champs de saisie (avec grille pour l'alignement)
row_counter = 0

tk.Label(main_frame, text="Nom d'utilisateur MySQL:").grid(row=row_counter, column=0, sticky="w", pady=5); row_counter += 1
user_entry.grid(row=row_counter-1, column=1, pady=5)

tk.Label(main_frame, text="Mot de passe MySQL:").grid(row=row_counter, column=0, sticky="w", pady=5); row_counter += 1
password_entry.grid(row=row_counter-1, column=1, pady=5)

tk.Label(main_frame, text="Hôte MySQL:").grid(row=row_counter, column=0, sticky="w", pady=5); row_counter += 1
host_entry.grid(row=row_counter-1, column=1, pady=5)

tk.Label(main_frame, text="Port MySQL (optionnel):").grid(row=row_counter, column=0, sticky="w", pady=5); row_counter += 1
port_entry.grid(row=row_counter-1, column=1, pady=5)

tk.Label(main_frame, text="Nom de la base de données:").grid(row=row_counter, column=0, sticky="w", pady=5); row_counter += 1
name_entry.grid(row=row_counter-1, column=1, pady=5)

# Champ pour le chemin de mysqldump local
mysqldump_frame = tk.Frame(main_frame)
mysqldump_frame.grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=10)
tk.Label(mysqldump_frame, text="Chemin de mysqldump:").grid(row=0, column=0, sticky="w", pady=5)
mysqldump_entry = tk.Entry(mysqldump_frame, width=35, textvariable=mysqldump_path_var)
mysqldump_entry.grid(row=0, column=1, pady=5, padx=(0,5))
mysqldump_browse_button = tk.Button(mysqldump_frame, text="Parcourir", command=browse_mysqldump_path)
mysqldump_browse_button.grid(row=0, column=2, pady=5, padx=5)
row_counter += 1

# Sélecteur de dossier de sortie
output_folder_frame = tk.Frame(main_frame)
output_folder_frame.grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=5)
tk.Label(output_folder_frame, text="Dossier de sortie:").grid(row=0, column=0, sticky="w", pady=5)
output_folder_label = tk.Label(output_folder_frame, textvariable=output_folder_path, wraplength=250, justify="left")
output_folder_label.grid(row=0, column=1, sticky="w", pady=5, padx=(0,5))
select_folder_button = tk.Button(output_folder_frame, text="Choisir", command=select_output_folder)
select_folder_button.grid(row=0, column=2, pady=5, padx=5)
row_counter += 1

# Boutons d'action
button_frame = tk.Frame(main_frame)
button_frame.grid(row=row_counter, column=0, columnspan=3, pady=20)

dump_button = tk.Button(button_frame, text="Lancer le Dump et ZIP", command=run_dump_in_thread, bg="#4CAF50", fg="black", padx=15, pady=8, font=("Arial", 10, "bold"))
dump_button.pack(side=tk.LEFT, padx=10)

open_folder_button = tk.Button(button_frame, text="Ouvrir le dossier de sortie", command=open_last_output_folder, state=tk.DISABLED, bg="#008CBA", fg="white", padx=15, pady=8, font=("Arial", 10))
open_folder_button.pack(side=tk.LEFT, padx=10)

row_counter += 1

# Étiquette de statut
status_label = tk.Label(main_frame, text="Prêt.", fg="blue", font=("Arial", 10, "italic"))
status_label.grid(row=row_counter, column=0, columnspan=3, pady=5)

# Charger les préférences au démarrage de l'application
load_preferences()

# Lancer la boucle principale de Tkinter
window.mainloop()
