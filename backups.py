###########################################################################################
#
# TITRE          : Script de sauvegarde avec Ansible

# DESCRIPTION    : 
#  Sauvegarde un répertoire dans un serveur ciblé. La sauvegarde est mis au format zip
#  et également copié dans un répertoire FTP local. A chaque sauvegarde deposée, quand 
# la quantité de sauvegarde maximum est dépassée, la sauvegarde la plus vieille est 
#  supprimée. La sauvegarde zip d'origine sur le serveur ciblé est aussi supprimée.
#
# AUTEUR         : Sylvain VIGIER
# DATE           : 23/09/2021
# https://github.com/Sylvain6363
#
###########################################################################################

#!/usr/bin/python3
# -*- coding: utf-8 -*-# 

########################## MODULES ########################################################

from datetime import datetime  # module pour obtenir la date et l'heure
from pathlib import Path  # module pour obtenir le chemin du répertoire à sauvegarder
import zipfile  # module pour créer des archives au format zip
import os  # module qui intéragit avec le système d'exploitation
from ftplib import FTP  # module permettant la connexion FTP 

########################## VARIABLES ######################################################

# variable permettant la connexion au serveur FTP 
ftp = FTP()  
# variable nom du serveur ciblé ( le playbook modifie cette variable )
srv = 'SRV-WORDPRESS'
# variable nom du dossier à sauvegarder ( le playbook modifie cette variable )
nomdossier = "bitnami"
# variable qui correspond a /nomdossier ( le playbook modifie cette variable )
Dossier = f"/{nomdossier}"
# variable chemin du dossier à sauvegarder
Chemindossier = Path(Dossier) 
# variable adresse ip du serveur FTP
host = "192.168.100.12" 
# variable identifiant FTP
user = "aic"
# variable mot de passe FTP
password = "aic"
# variable du nom que portera la sauvegarde (Backup-date-jour.mois.année*heureminuteseconde-nomdossieràsauvegarder.zip)
archive = f'Backup-{datetime.now().strftime("%d.%m.%Y*%Hh%Mm%Ss")}-{Chemindossier.name}.zip' 
# variable représentant la quantité maximum de sauvegarde que le serveur FTP va stocker 
QUANTITE_DE_SAUVEGARDE_MAX = 7 

########################## FONCTIONS ######################################################

# fonction qui affiche la liste de tous les chemins de fichiers et dossiers dans le répertoire à sauvegarder
# dossier est le répertoire à sauvegarder
def listedossierasauvegarder(dossier):
    # créer une variable fichierdossier a partir de la fonction recupfichierdansdossier
    fichierdossier = recupfichiersdansdossier(dossier)
    # pour tous le contenu dans fichierdossier, affiche son contenu
    for nom_fichier in fichierdossier:
        print(nom_fichier)
    print("")

# fonction de création de l'archive zip
# fichierliste represente le contenu du dossier à sauvegarder
# nomarchive est le nom de fichier de l'archive avec un chemin complet
def creerArchive(fichierliste, nomarchive):
    # essaye ceci sinon le script s'arrete
    try:
        # variable a pour créer une archive qui portera le nom nomarchive avec une compression standard deflated
        a = zipfile.ZipFile(nomarchive, 'w', zipfile.ZIP_DEFLATED)
        # pour tout le contenu dans fichierliste, ecrit le dans l'archive
        for f in fichierliste:  
            a.write(f)
        a.close()
        # si l'archive est créée alors on continu
        return True
    except: return False

# fonction qui récupère tous le contenu du dossier à sauvegarder, qui l'insert dans un dictionnaire, et renvoit son contenu.
# dossier est le répertoire à sauvegarder
def recupfichiersdansdossier(dossier):
    # tous les fichiers du dossier à sauvegarder iront dans ce dictionnaire
    fichiersdossier = []
    # parcourir le répertoire et les sous-répertoires
    for racine, dossiers, fichiers in os.walk(dossier):
        # joindre les deux chaînes afin de former le chemin de fichier complet.
        for nomfichier in fichiers:
            cheminfichier = os.path.join(racine, nomfichier)
            # ajouter le contenu au dictionnaire fichiersdossier
            fichiersdossier.append(cheminfichier)
    # renvoit tous les chemins de fichiers du dossier
    return fichiersdossier 

# fonction qui permet d'obtenir la liste brute des sauvegardes déjà presentes sur le serveur FTP de les insérer dans un dictionnaire
# et qui renvoit son contenu
def obtenirsauvegardespresentes():
    # tous les fichiers du dossier qui contient les sauvegardes iront dans ce dictionnaire
    sauvegardes = [] 
    # ajoute la liste des sauvegardes au dictionnaire sauvegardes 
    ftp.retrlines('NLST', sauvegardes.append)
    # renvoit la liste des sauvegardes
    return sauvegardes

# fonction qui permet d'afficher la liste des sauvegardes de manière plus lisible
def afficherlistesauvegardes():
    # permet d'afficher seulement les noms complets des sauvegardes
    for ligne in sorted(obtenirsauvegardespresentes()):
        x = ligne.split(".")
        formats=["zip"]
        if x[-1] in formats:
            print("-", ligne)
    print("")

# fonction qui supprime la plus ancienne des 6 sauvegardes maximum autorisées deja presentes sur le serveur FTP    
def suppressionsauvegarde():
    # variable representant la liste dans l'ordre des sauvegardes presentes dans le répertoire FTP
    liste_des_sauvegardes = list(sorted(obtenirsauvegardespresentes()))  
    # tant que la liste des sauvegardes est supérieur ou égal au nombre maximum de sauvegardes autorisées à être stockées
    while len(liste_des_sauvegardes) >= QUANTITE_DE_SAUVEGARDE_MAX:  
        # supprimer la sauvegarde la plus ancienne
        sauvegarde_a_supprimer = liste_des_sauvegardes.pop(0)
        ftp.delete(sauvegarde_a_supprimer)

# fonction qui créé le dossier (porte le meme nom que le repertoire a sauvegarder) ou envoyer les sauvegardes sur le serveur FTP
# nomdudossier est le nom du répertoire à sauvegarder 
def repertoiresauvegarde(nomdudossier):
    # Si le nom de dossier n'existe pas dans le dossier racine du serveur FTP, il le créé et se place par défaut sur celui-ci
    if not nomdudossier in ftp.nlst():
        ftp.mkd(nomdudossier)
        ftp.cwd(nomdudossier)
    # Sinon il existe déjà et se place par défaut sur celui-ci
    else:
        ftp.cwd(nomdudossier)

# fonction qui stock la sauvegarde zippée dans le répertoire FTP 
def stocklasauvegarde(arc):
    ftp.storbinary('STOR ' + arc, open(arc, 'rb'))

# fonction principale
def main():
    # affiche un titre Sauvegardes Zip FTP
    print("---------------------------")
    print("---------------------------")
    print("--  Sauvegardes Zip FTP  --")
    print("---------------------------")
    print("------ " + (srv) + " ------")
    print("\n=====")
    print("Les fichiers suivants seront compressés:")
    # lance la fonction listedossierasauvegarder qui point sur le dossier à sauvegarder,
    # il affiche tous les chemins des fichiers du dossier
    listedossierasauvegarder(Dossier)
    
    # lance la fonction creerArchive avec les parametres fonction recupfichiersdansdossier + le nom de l'archive
    # cela va créer une sauvegarde locale dans le serveur à sauvegarder
    creerArchive(recupfichiersdansdossier(Dossier), archive) 
    print("=====")
    print("Les fichiers sont Zippés")
    print("=====\n")
    
    print("=====")
    print("Connexion au Serveur FTP")
    # permet la connexion au serveur FTP avec les variables host, user et password
    ftp.connect(host)
    ftp.login(user,password)
    print("=====\n")

    print("=====")
    print("Obtenir la liste des Sauvegardes déjà présentes")
    # lance la fonction repertoiresauvegarde qui permet de se placer sur un autre dossier que le dossier racine du serveur FTP
    repertoiresauvegarde(srv)
    # lance la fonction afficherlistesauvegardes qui affiche la liste des sauvegardes du serveur déjà presentes depuis le serveur FTP 
    afficherlistesauvegardes()
    # affiche le nombre de fichiers trouvés dans le dossier contenant les sauvegardes
    print(str(len(obtenirsauvegardespresentes())) + " fichiers trouvés")
    print("=====\n")
    
    print("=====")
    print("Suppression de la sauvegarde la plus ancienne")
    # lance la fonction qui supprime la sauvegarde la plus ancienne des 7 max autorisées sur le serveur FTP
    suppressionsauvegarde()
    print("=====\n")

    print("=====")
    print("Upload de la nouvelle Sauvegarde Zippée")
    # lance la fonction qui stock la sauvegarde dans le dossier FTP en utilisant le parametre archive, c'est a dire le nom que portera l'archive
    stocklasauvegarde(archive)
    print("=====\n")
    # lance a nouveau la fonction afficherlistesauvegardes qui affiche la liste des sauvegardes à present modifiées depuis le serveur FTP
    afficherlistesauvegardes()
    print("=====")
    print("Fermeture de la Connexion")
    # deconnexion au serveur FTP
    ftp.close()
    
    print("=====\n")
    
    print("=====")
    print("Supprimer la sauvegarde ZIP locale")
    # suppression de la sauvegarde zip locale sur le serveur à sauvegarder 
    os.remove(archive)
    print("=====\n")
# si on lance le script et que des instructions sont dans la fonction principale, elle seront executées.
# ces instructions ne seront pas executées si le script est importé comme module.
if __name__ == '__main__':
    main()


