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

from datetime import datetime  
from pathlib import Path  
import zipfile  
import os  
from ftplib import FTP  

########################## VARIABLES ######################################################

ftp = FTP() 
srv = 'SRV-WORDPRESS'
nomdossier = "bitnami"
Dossier = f"/{nomdossier}"
Chemindossier = Path(Dossier) 
host = "192.168.100.12" 
user = "aic"
password = "aic"
archive = f'Backup-{datetime.now().strftime("%d.%m.%Y*%Hh%Mm%Ss")}-{Chemindossier.name}.zip' 
QUANTITE_DE_SAUVEGARDE_MAX = 7 

########################## FONCTIONS ######################################################

def listedossierasauvegarder(dossier):
    fichierdossier = recupfichiersdansdossier(dossier)
    for nom_fichier in fichierdossier:
        print(nom_fichier)
    print("")

def creerArchive(fichierliste, nomarchive):
    try:
        a = zipfile.ZipFile(nomarchive, 'w', zipfile.ZIP_DEFLATED)
        for f in fichierliste:  
            a.write(f)
        a.close()
        return True
    except: return False

def recupfichiersdansdossier(dossier):
    fichiersdossier = []
    for racine, dossiers, fichiers in os.walk(dossier):
        for nomfichier in fichiers:
            cheminfichier = os.path.join(racine, nomfichier)
            fichiersdossier.append(cheminfichier)
    return fichiersdossier 

def obtenirsauvegardespresentes():
    sauvegardes = [] 
    ftp.retrlines('NLST', sauvegardes.append)
    return sauvegardes

def afficherlistesauvegardes():
    for ligne in sorted(obtenirsauvegardespresentes()):
        x = ligne.split(".")
        formats=["zip"]
        if x[-1] in formats:
            print("-", ligne)
    print("")
    
def suppressionsauvegarde():
    liste_des_sauvegardes = list(sorted(obtenirsauvegardespresentes()))  
    while len(liste_des_sauvegardes) >= QUANTITE_DE_SAUVEGARDE_MAX:  
        sauvegarde_a_supprimer = liste_des_sauvegardes.pop(0)
        ftp.delete(sauvegarde_a_supprimer)

def repertoiresauvegarde(nomdudossier):
    if not nomdudossier in ftp.nlst():
        ftp.mkd(nomdudossier)
        ftp.cwd(nomdudossier)
    else:
        ftp.cwd(nomdudossier)
    
def stocklasauvegarde(arc):
    ftp.storbinary('STOR ' + arc, open(arc, 'rb'))

def main():
    print("---------------------------")
    print("---------------------------")
    print("--  Sauvegardes Zip FTP  --")
    print("---------------------------")
    print("------ " + (srv) + " ------")
    print("\n=====")
    print("Les fichiers suivants seront compressés:")

    listedossierasauvegarder(Dossier)
    print(nomfichier)
    creerArchive(recupfichiersdansdossier(Dossier), archive) 
    print("=====")
    print("Les fichiers sont Zippés")
    print("=====\n")
    
    print("=====")
    print("Connexion au Serveur FTP")
  
    ftp.connect(host)
    ftp.login(user,password)
    print("=====\n")

    print("=====")
    print("Obtenir la liste des Sauvegardes déjà présentes")

    repertoiresauvegarde(srv)

    afficherlistesauvegardes()
 
    print(str(len(obtenirsauvegardespresentes())) + " fichiers trouvés")
    print("=====\n")
    
    print("=====")
    print("Suppression de la sauvegarde la plus ancienne")
 
    suppressionsauvegarde()
    print("=====\n")

    print("=====")
    print("Upload de la nouvelle Sauvegarde Zippée")

    stocklasauvegarde(archive)
    print("=====\n")
  
    afficherlistesauvegardes()
    print("=====")
    print("Fermeture de la Connexion")
   
    ftp.close()
    
    print("=====\n")
    
    print("=====")
    print("Supprimer la sauvegarde ZIP locale")
   
    os.remove(archive)
    print("=====\n")

if __name__ == '__main__':
    main()
 

