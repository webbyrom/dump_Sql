import tkinter as tk
from tkinter import messagebox, filedialog
import os
import subprocess
import datetime
import getpass # Bien que getpass ne soit pas utilisé directement avec Entry widgets, c'est bon de l'avoir pour d'autres usages ou si on change d'approche.

def dump_mysql_database_gui():
    """
    Récupère les informations de l'interface graphique et exécute la commande mysqldump.
    """
    # Récupérer les valeurs des champs de l'interface
    db_user = user_entry.get()
    db_password = password_entry.get()
    db_host = host_entry.get()
    db_port = port_entry.get()
    db_name = name_entry.get()

    # --- Configuration du chemin mysqldump ---
    # Cette variable doit être configurée une fois pour toutes selon ton OS et ton installation MAMP.
    # Pour un script distribuable, il faudrait soit une détection auto plus complexe,
    # soit laisser l'utilisateur le configurer via l'interface.
    # Pour l'instant, assure-toi que ce chemin correspond à ton installation MAMP PRO sur Mac.
    MYSQLDUMP_PATH = "mysqldump"
    # Si c'était pour Windows et MAMP dans C:\MAMP:
    # MYSQLDUMP_PATH = "C:\\MAMP\\bin\\mysql\\mysql5.7.X\\bin\\mysqldump.exe"

    if not os.path.exists(MYSQLDUMP_PATH):
        messagebox.showerror("Erreur de configuration",
                             f"mysqldump n'a pas été trouvé à l'emplacement spécifié : {MYSQLDUMP_PATH}\n"
                             "Veuillez vérifier le chemin dans le code du script.")
        return

    # Vérifier que les champs obligatoires ne sont pas vides
    if not db_user or not db_host or not db_name:
        messagebox.showwarning("Champs manquants", "Veuillez remplir au moins l'utilisateur, l'hôte et le nom de la base de données.")
        return

    # --- Définir le nom et le chemin du fichier de sortie ---
    # Le fichier sera enregistré sur le bureau par défaut, mais on peut ajouter un sélecteur de dossier.
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.expanduser("~"), "Desktop") # Par défaut sur le bureau
    output_file = os.path.join(output_dir, f"{db_name}_{timestamp}.sql")

    # Si l'utilisateur a sélectionné un dossier de sortie différent
    if output_folder_path.get():
        output_file = os.path.join(output_folder_path.get(), f"{db_name}_{timestamp}.sql")


    # --- Construire la commande mysqldump ---
    command = [
        MYSQLDUMP_PATH,
        f"-h{db_host}",
        f"-u{db_user}",
        f"-p{db_password}", # Le mot de passe est directement passé ici
    ]

    if db_port: # Si le port est renseigné
        command.append(f"-P{db_port}")

    command.append(db_name) # Nom de la base de données en dernier

    # Afficher les informations dans la console (pour le débogage) et dans la GUI
    status_label.config(text=f"Sauvegarde de '{db_name}' depuis '{db_host}'...")
    window.update_idletasks() # Force la mise à jour de l'interface

    # --- Exécuter la commande ---
    try:
        with open(output_file, 'w') as f:
            process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE, text=True)
            stderr_output = process.communicate()[1] # Attend la fin du processus

        if process.returncode == 0:
            messagebox.showinfo("Succès", f"Dump créé avec succès !\nFichier : {output_file}")
            status_label.config(text="Opération terminée.")
        else:
            messagebox.showerror("Erreur",
                                 f"Une erreur s'est produite lors du dump (Code : {process.returncode}).\n"
                                 f"Message : {stderr_output.strip()}")
            status_label.config(text="Erreur lors du dump.")

    except FileNotFoundError:
        messagebox.showerror("Erreur", f"Le programme mysqldump n'a pas été trouvé à l'emplacement : {MYSQLDUMP_PATH}\n"
                                       "Veuillez vérifier que le chemin est correct.")
        status_label.config(text="Erreur : mysqldump introuvable.")
    except Exception as e:
        messagebox.showerror("Erreur inattendue", f"Une erreur inattendue s'est produite : {e}")
        status_label.config(text="Erreur inattendue.")

def select_output_folder():
    """Ouvre une boîte de dialogue pour sélectionner le dossier de sortie."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_folder_path.set(folder_selected)
        output_folder_label.config(text=f"Dossier de sortie : {folder_selected}")


# --- Configuration de l'interface Tkinter ---
window = tk.Tk()
window.title("MySQL Database Dumper")
window.geometry("500x450") # Taille initiale de la fenêtre

# Cadre principal pour un meilleur alignement
main_frame = tk.Frame(window, padx=20, pady=20)
main_frame.pack(expand=True, fill="both")

# Labels et champs de saisie
tk.Label(main_frame, text="Nom d'utilisateur MySQL:").grid(row=0, column=0, sticky="w", pady=5)
user_entry = tk.Entry(main_frame, width=40)
user_entry.grid(row=0, column=1, pady=5)
user_entry.insert(0, "root") # Valeur par défaut pour MAMP

tk.Label(main_frame, text="Mot de passe MySQL:").grid(row=1, column=0, sticky="w", pady=5)
password_entry = tk.Entry(main_frame, width=40, show="*") # show="*" masque le mot de passe
password_entry.grid(row=1, column=1, pady=5)
password_entry.insert(0, "root") # Valeur par défaut pour MAMP

tk.Label(main_frame, text="Hôte MySQL:").grid(row=2, column=0, sticky="w", pady=5)
host_entry = tk.Entry(main_frame, width=40)
host_entry.grid(row=2, column=1, pady=5)
host_entry.insert(0, "localhost") # Valeur par défaut pour MAMP

tk.Label(main_frame, text="Port MySQL (optionnel):").grid(row=3, column=0, sticky="w", pady=5)
port_entry = tk.Entry(main_frame, width=40)
port_entry.grid(row=3, column=1, pady=5)
# port_entry.insert(0, "3306") # Si tu veux un port par défaut

tk.Label(main_frame, text="Nom de la base de données:").grid(row=4, column=0, sticky="w", pady=5)
name_entry = tk.Entry(main_frame, width=40)
name_entry.grid(row=4, column=1, pady=5)

# Sélecteur de dossier de sortie
output_folder_path = tk.StringVar()
output_folder_label = tk.Label(main_frame, textvariable=output_folder_path, wraplength=300, justify="left")
output_folder_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
output_folder_path.set(f"Dossier de sortie : {os.path.join(os.path.expanduser('~'), 'Desktop')}") # Définit le bureau par défaut

select_folder_button = tk.Button(main_frame, text="Choisir le dossier de sortie", command=select_output_folder)
select_folder_button.grid(row=6, column=0, columnspan=2, pady=10)

# Bouton de dump
dump_button = tk.Button(main_frame, text="Lancer le Dump", command=dump_mysql_database_gui)
dump_button.grid(row=7, column=0, columnspan=2, pady=20)

# Étiquette de statut (pour les messages d'avancement)
status_label = tk.Label(main_frame, text="Prêt.", fg="blue")
status_label.grid(row=8, column=0, columnspan=2, pady=5)

# Lancer la boucle principale de Tkinter
window.mainloop()
