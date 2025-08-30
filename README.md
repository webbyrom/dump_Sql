MySQL Database Dumper

Ce script Python est une interface graphique simple qui permet d'exporter (de "dumper") une base de données MySQL à l'aide de l'outil en ligne de commande mysqldump. Il est particulièrement utile pour les développeurs qui utilisent un environnement local comme MAMP ou WAMP et qui ont besoin de créer rapidement des sauvegardes de leurs bases de données.

Fonctionnalités ✨

Interface Graphique (GUI) : Utilise la bibliothèque tkinter pour une interface utilisateur conviviale.

Exportation de la base de données : Exécute la commande mysqldump pour créer un fichier .sql.

Sauvegarde horodatée : Les fichiers de sauvegarde sont nommés automatiquement avec la date et l'heure pour éviter d'écraser les sauvegardes précédentes (ex: nom_base_de_donnees_20250830_070916.sql).

Chemin de sortie configurable : Permet de choisir où le fichier de sauvegarde sera enregistré.

Validation des champs : Vérifie que les informations nécessaires pour la connexion à la base de données sont bien renseignées.

Prérequis 🛠️

Avant d'utiliser ce script, assurez-vous d'avoir les éléments suivants :

Python 3 : Le script est écrit en Python 3.

mysqldump : L'outil de ligne de commande mysqldump doit être accessible depuis votre terminal. Si vous utilisez MAMP, il se trouve généralement dans le dossier bin de votre installation MySQL.

Configuration ⚙️

Mise à jour du chemin mysqldump : Le script est pré-configuré pour un environnement MAMP sur Mac. Si votre installation est différente, vous devrez modifier le chemin dans le code.

Trouvez la ligne suivante dans le script :

Python
MYSQLDUMP_PATH = "mysqldump"
Remplacez "mysqldump" par le chemin d'accès complet à l'exécutable.

Exemple MAMP sur Mac : "/Applications/MAMP/Library/bin/mysqldump"

Exemple MAMP sur Windows : "C:\\MAMP\\bin\\mysql\\bin\\mysqldump.exe"

Utilisation 🚀

Ouvrez votre terminal ou votre invite de commande.

Naviguez jusqu'au dossier où se trouve le script mysql_dumper.py (assurez-vous d'avoir bien sauvegardé le code sous ce nom).

Exécutez le script avec la commande Python :

Bash
python3 mysql_dumper.py
Remplissez les informations de votre base de données dans les champs de l'interface.

Cliquez sur "Lancer le Dump" pour créer votre sauvegarde.

Le fichier .sql sera créé dans le dossier de sortie que vous avez sélectionné (le bureau par défaut).