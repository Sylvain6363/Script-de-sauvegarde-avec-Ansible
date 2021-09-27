

# Script de sauvegarde avec Ansible

Réaliser des sauvegardes complètes du répertoire d'un ou plusieurs serveurs vers un serveur FTP local à l'aide d'un script python et d'Ansible.
Ces sauvegardes, une fois executées, sont déposées chaque jour au format zip sur le serveur FTP avec un roulement de 7 sauvegardes maximum.

## Démarrage 

Ces instructions vous permettront d'obtenir une copie du projet opérationnel sur votre ordinateur local à des fins de développement et de test. Voir le déploiement pour des notes sur la façon de déployer le projet sur un système en direct.

### Prerequis 

- Un logiciel de virtualisation ( Dans mon cas j'ai utilisé VirtualBox v6.1.22)
- Créer 4 VMs Debian 10 Buster pour le serveur web, le serveur de fichiers, le serveur ftp et le poste administrateur (node manager)
- Que les 4 VMs disposent d'une connexion internet
- Les VMs doivent être sur le même réseau

### Maquette de l'architecture utilisée

![Maquette réalisée sous GNS3 v2.2.21](https://github.com/Sylvain6363/Script-de-sauvegarde-avec-Ansible/blob/main/Capture%20d%E2%80%99%C3%A9cran%202021-09-24%20130233.png)

## Installation

#### SERVEUR WEB
Installer la VM avec une image `bitnami-wordpress-5.8.0-14-r05-linux-debian-10-x86_64-nami.ova` du site [bitnami.com](https://bitnami.com/stack/wordpress/virtual-machine)
Configurer l'interface réseau :

	nano /etc/network/interfaces


    auto enp0s3
    iface enp0s3 inet static
    address 192.168.100.11/24
    gateway 192.168.100.254

Redemarrer le service réseau :

	systemctl restart networking

Mise à jour du gestionnaire de paquet apt : 

	apt update

Installer le paquet openssh-server

	apt install openssh-server

Ajouter `PermitRootLogin yes` au fichier `sshd_config` : 

	nano /etc/ssh/sshd_config 

Redemarrer le service ssh :

	systemctl restart ssh

#### SERVEUR FTP  
Installer la VM avec une image `debian-10.9.0-amd64-xfce-CD-1.iso`
Configurer l'interface réseau :

	nano /etc/network/interfaces

	auto enp0s3
	iface enp0s3 inet static
	address 192.168.100.12/24
	gateway 192.168.100.254

Redemarrer le service réseau :

	systemctl restart networking

Installation du paquet proftpd : 

	apt-get install proftpd

Créer le groupe ftpgroup :

	addgroup ftpgroup

Créer l'utilisateur FTP aic ainsi que son répertoire par défaut `/ftpshare` :

	adduser aic -home /ftpshare

Ajouter l'utilisateur aic au group ftpgroup :

	adduser aic ftpgroup

Appliquer les permissions sur le répertoire `/ftpshare` :

	chmod -R 1777 /ftpshare/

Configurer le fichier `ftp.conf` :

	nano /etc/proftpd/conf.d/ftp.conf

	ServerName         "SRV-FTP"	#la bannière qui apparaît à la connexion
	UseIPv6            off			# Pas de connexion IPv6
	RootLogin          off 			# Interdire le login en root
	RequireValidShell  on 			# Vérifie que les utilisateurs aient un shell valide ou non
	Port               21			# Le port 21 est le port FTP standard
	DefaultRoot  ~					# pour restreindre l'accès des utilisateurs à leurs dossiers de départ uniquement
	<Limit LOGIN>
	    DenyGroup !ftpgroup			# interdire les connexions hors du groupe ftpgroup
	</Limit>
	<IfModule mod_ctrls.c>
	ControlsEngine        off
	ControlsMaxClients    2                                #definition du nombre de connexions max par clients
	ControlsLog           /var/log/proftpd/controls.log
	ControlsInterval      5
	ControlsSocket        /var/run/proftpd/proftpd.sock
	</IfModule>

Redemarrer le service FTP :

	systemctl restart proftpd

Le répertoire `/ftpshare` doit être accessible avec les identifiants:
* ID aic
* PASS aic

#### SERVEUR DE FICHIERS
Installer la VM avec une image `debian-10.9.0-amd64-xfce-CD-1.iso`
Configurer l'interface réseau :

	nano /etc/network/interfaces

	auto enp0s3
	iface enp0s3 inet static
	address 192.168.100.13/24
	gateway 192.168.100.254

Redemarrer le service réseau :

	systemctl restart networking

Mise à jour du gestionnaire de paquet apt : 

	apt update

Installer le paquet openssh-server

	apt install openssh-server

Ajouter `PermitRootLogin yes` au fichier `sshd_config` : 

	ano /etc/ssh/sshd_config 

#### POSTE ADMINISTRATEUR (node manager)
Installer la VM avec une image `debian-10.9.0-amd64-xfce-CD-1.iso`
Configurer l'interface réseau :

	nano /etc/network/interfaces

	auto enp0s3
	iface enp0s3 inet static
	address 192.168.100.100/24
	gateway 192.168.100.254

Redemarrer le service réseau :

	systemctl restart networking

Insérer dans le fichier `/etc/hosts` :

	192.168.100.11  SRV-WORDPRESS
	192.168.100.12  SRV-FTP
	192.168.100.13  SRV-FILES

Mettre à jour le gestionnaire de paquet apt : 

	apt update

Installer le paquet pip3 :

	apt install python3-pip

Installer l'environnement virtuel : 

	apt install python3-venv sshpass

Créer l'utilisateur `user-ansible`

	adduser user-ansible

Donner les droits root a l'utilisateur user-ansible en ajoutant `user-ansible ALL=(ALL:ALL) ALL` au fichier sudoers

	nano /etc/sudoers

Passer sur l'utilisateur `user-ansible`

	su - user-ansible

Créer l'environnement virtuel dans un répertoire que nous nommerons "ansible"

	python3 -m venv ansible

Activer l'environnement virtuel

	source ansible/bin/activate

Mettre à jour pip3

	pip3 install --upgrade pip

Installer `ansible 2.9.5` ( Dans cette maquette j'utilise Ansible v2.9.5)

	pip3 install ansible==2.9.5

Créer l'inventaire `/home/user-ansible/inventaire.ini` :

	[serveur_web]
	SRV-WORDPRESS
	[serveur_fichiers]
	SRV-FILES
	[all:vars]
	vars_serveur_web=bitnami
	vars_serveur_fichiers=partagefichiers
	ansible_user=user-ansible
	ansible_ssh_pass=ansible
	ansible_become_pass=ansible

Créer le fichier de config d'ansible `/home/user-ansible/ansible.cfg` :

	[defaults]
	inventory  = /home/user-ansible/inventaire.ini
	deprecation_warnings  =  False
	interpreter_python  =  /usr/bin/python3

Installer `python3.7` sur les serveurs avec la commande :

	ansible -i inventaire.ini -m raw -a "apt-get install -y python3.7" SRV-WORDPRESS --user root --ask-pass
	ansible -i inventaire.ini -m raw -a "apt-get install -y python3.7" SRV-FILES --user root --ask-pass

Créer un mot de passe chiffré avec la commande :

	ansible localhost -i inventaire.ini -m debug -a "msg={{ 'ansible' | password_hash('sha512', 'sceretsalt') }}"

Créer les utilisateurs user-ansible avec un mot de passe chiffré sur le serveur web et le serveur de fichiers :

	ansible -i inventaire.ini -m user -a 'name=user-ansible password=$6$sceretsalt$WuWJ0D3fk0MdiwZoAihkPijW0jPLyrYkvfuaoYfREjCk31ZT9Uvrp6Ue1ODCD13zLcuAUPoPTMH3wV2oohP7G0' --user root --ask-pass all

Ajouter les droits sudo a aux utilisateurs user-ansible des serveurs :

	ansible -i inventaire.ini -m user -a 'name=user-ansible groups=sudo append=yes ' --user root --ask-pass all

Créer les clés de sécurité sans passphrase :

	ssh-keygen -t ecdsa

Ajouter les clés aux utilisateurs user-ansible des serveurs :

	ansible -i inventaire.ini -m authorized_key -a 'user=user-ansible state=present key="{{ lookup("file", "/home/user-ansible/.ssh/id_ecdsa.pub") }}"' --user user-ansible --ask-pass --become --ask-become-pass all

Créer le role serveur `serveurs_sauvegardes` :

	ansible-galaxy init serveurs_sauvegardes

Editer le fichier dans tasks `/home/user-ansible/roles/serveurs_sauvegardes/tasks/main.yml` :

    ---
	  - name: "Installe le paquet ftp s'il n'est pas présent sur le serveur"
	    apt:
	      name: ftp
	      update_cache: yes
	      cache_valid_time: 60
	      state: latest
	  - name: "Executer le script de sauvegarde"
	    script: /home/user-ansible/backups.py
	    args:
	      executable: python3 
	    register: python_result
	  - debug: var=python_result.stdout_lines

Créer le playbook `serveurs_sauvegardes.yml` :

	nano /home/user-ansible/serveurs_sauvegardes.yml

    ---
	  - name: "Remplacement du chemin du script backups.py"
				  hosts: localhost
				  tasks:
				    - name: "Recupere le nom du dossier à sauvegarder"
				      shell: "grep 'vars_serveur_web=*' /home/user-ansible/inventaire.ini | cut -d = -f 2"
				      register: Dossier_serveur_web
				    - name: "Remplacer le nom du serveur dans le script backups.py"
				      lineinfile:
				        dest: /home/user-ansible/backups.py
				        regexp: 'srv =.*'
				        line: "srv = '{{ groups['serveur_web'][0] }}'"
				    - name: "Remplacer le nom du dossier à sauvegarder dans le script backups.py"
				      lineinfile:
				        dest: /home/user-ansible/backups.py
				        regexp: 'nomdossier =.*'
				        line: 'nomdossier = "{{Dossier_serveur_web.stdout}}"'
				- name: "Lancement du script de sauvegarde"
				  hosts: serveur_web
				  tasks:
				  roles:
				    - role: "serveurs_sauvegardes"
				- name: "Recuperation du dossier et lancement du script pour le groupe serveur_fichiers"
				  hosts: localhost
				  tasks:
				    - name: "Recupere le nom du dossier à sauvegarder"
				      shell: "grep 'vars_serveur_fichiers=*' /home/user-ansible/inventaire.ini | cut -d = -f 2"
				      register: Dossier_serveur_fichiers
				    - name: "Remplacer le nom du dossier à sauvegarder dans le script backups.py"
				      lineinfile:
				        dest: /home/user-ansible/backups.py
				        regexp: 'nomdossier =.*'
				        line: 'nomdossier = "{{Dossier_serveur_fichiers.stdout}}"'
				    - name: "Remplacer le nom du serveur dans le script backups.py"
				      lineinfile:
				        dest: /home/user-ansible/backups.py
				        regexp: 'srv =.*'
				        line: "srv = '{{ groups['serveur_fichiers'][0] }}'"
				- name: "Lancement du script de sauvegarde"
				  hosts: serveur_fichiers
				  tasks:
				  roles:
				    - role: "serveurs_sauvegardes"

## Utilisation

Ici le script est configuré pour sauvegarder le répertoire "bitnami" à la racine du serveur web nommé "SRV-WORDPRESS", et le répertoire "partagefichiers" à la racine du serveur de fichiers nommé "SRV-FILES"

Ce script, tel qu'il est actuellement, est prévu pour faire la sauvegarde d'un répertoire par groupe. On peut le constater sur le fichier inventaire.ini, nous avons un groupe [serveur_web] qui contient le nom du serveur ou son ip ainsi que la variable dans le groupe [all:vars] qui indique le chemin du répertoire a sauvegarder pour ce serveur, puis également la même chose pour le groupe serveur_fichiers.

	[serveur_web]
	SRV-WORDPRESS
	[serveur_fichiers]
	SRV-FILES
	[all:vars]
	vars_serveur_web=bitnami
	vars_serveur_fichiers=partagefichiers

Si nous voulons faire la sauvegarde du répertoire `/etc/ssh` d'un serveur avec une ip `192.168.100.50`, on peut modifier comme cela :

	[serveur_fichiers]
	192.168.100.50
	[all:vars]
	vars_serveur_fichiers=etc/ssh

La configuration du serveur FTP se renseigne directement sur le script python nommé backups.py

	host = "192.168.100.12" 
	user = "aic"
	password = "aic"

Nous pouvons maintenant lancer la commande `ansible-playbook` pour effectuer les sauvegardes comme ceci :*(être sur l'utilisateur "user-ansible" et avoir l'environnement virtuel activé)*

	ansible-playbook -i inventaire.ini --user user-ansible --become --ask-become-pass serveurs_sauvegardes.yml

Pour lancer la commande ansible-playbook de manière journalière avec crontab, nous aurons besoin de 3 autres variables dans le fichier `inventaire.ini` qui permettront d'oter les arguments d'authentification sur la commande `ansible-playbook`

	ansible_user=user-ansible
	ansible_ssh_pass=ansible
	ansible_become_pass=ansible

Nous avons également besoin de renseigner le chemin du fichier `inventaire.ini` dans le fichier de configuration d'ansible `ansible.cfg`, cela permettra également d'oter l'argument d'inventaire sur la commande ansible-playbook

	[defaults]
	inventory  = /home/user-ansible/inventaire.ini

Ces modifications effectués, nous pouvons à present effectuer les sauvegardes avec cette commande :

	ansible-playbook --become serveurs_sauvegardes.yml

Nous pouvons maintenant ajouter la commande `0 21 * * * /home/user-ansible/.local/bin/ansible-playbook --become /home/user-ansible/serveurs_sauvegardes.yml -f 10 > /home/user-ansible/ansiblecrontab.log` au planificateur de tâches crontab. *(être sur l'utilisateur "user-ansible" et avoir l'environnement virtuel activé)*

	crontab -e

Les sauvegardes s'executeront donc tous les jours de la semaine à 21H et laisseront leurs resultats d'execution dans un fichier de log `home/user-ansible/ansiblecrontab.log`

## Modification possible

Si nous avons besoin de faire une sauvegarde a partir d'un autre serveur, mais qui possède le même dossier à sauvegarder que celui du groupe serveur_web, nous modifierons le fichier inventaire.ini comme ceci :

	[serveur_web]
	SRV-WORDPRESS
	SRV-WORDPRESS-2
	[all:vars]
	vars_serveur_web=bitnami

Nous aurons aussi besoin d'ajouter ce bloc dans le playbook `serveurs_sauvegardes.yml`

	- name: "Remplacement du chemin du script backups.py"
					  hosts: localhost
					  tasks:
					    - name: "Recupere le nom du dossier à sauvegarder"
					      shell: "grep 'vars_serveur_web=*' /home/user-ansible/inventaire.ini | cut -d = -f 2"
					      register: Dossier_serveur_web
					    - name: "Remplacer le nom du serveur dans le script backups.py"
					      lineinfile:
					        dest: /home/user-ansible/backups.py
					        regexp: 'srv =.*'
					        line: "srv = '{{ groups['serveur_web'][1] }}'"
					    - name: "Remplacer le nom du dossier à sauvegarder dans le script backups.py"
					      lineinfile:
					        dest: /home/user-ansible/backups.py
					        regexp: 'nomdossier =.*'
					        line: 'nomdossier = "{{Dossier_serveur_web.stdout}}"'
					- name: "Lancement du script de sauvegarde"
					  hosts: serveur_web
					  tasks:
					  roles:
					    - role: "serveurs_sauvegardes"

Si nous avons besoin de faire également une sauvegarde a partir d'un autre serveur, mais qu'il possède son propre dossier à sauvegarder, nous ajouterons au fichier inventaire.ini un nouveau groupe avec son serveur mais aussi une nouvelle variable du répertoire a sauvegarder depuis le groupe `all:vars` :

	[serveur_web]
	SRV-WORDPRESS
	[serveur_fichiers]
	SRV-FILES
	[serveur_profils]
	SRV-PROFILES
	[all:vars]
	vars_serveur_web=bitnami
	vars_serveur_fichiers=partagefichiers
	vars_serveur_profils=home

Nous aurons également besoin d'ajouter ce bloc dans le playbook `serveurs_sauvegardes.yml`

	- name: "Remplacement du chemin du script backups.py"
					  hosts: localhost
					  tasks:
					    - name: "Recupere le nom du dossier à sauvegarder"
					      shell: "grep 'vars_serveur_profils=*' /home/user-ansible/inventaire.ini | cut -d = -f 2"
					      register: Dossier_serveur_profils
					    - name: "Remplacer le nom du serveur dans le script backups.py"
					      lineinfile:
					        dest: /home/user-ansible/backups.py
					        regexp: 'srv =.*'
					        line: "srv = '{{ groups['serveur_profils'][0] }}'"
					    - name: "Remplacer le nom du dossier à sauvegarder dans le script backups.py"
					      lineinfile:
					        dest: /home/user-ansible/backups.py
					        regexp: 'nomdossier =.*'
					        line: 'nomdossier = "{{Dossier_serveur_profils.stdout}}"'
					- name: "Lancement du script de sauvegarde"
					  hosts: serveur_profils
					  tasks:
					  roles:
					    - role: "serveurs_sauvegardes"

## Auteur

* **Sylvain VIGIER** - [Sylvain6363](https://github.com/Sylvain6363)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Sylvain6363/Script-de-sauvegarde-avec-Ansible/blob/main/LICENSE) file for details


