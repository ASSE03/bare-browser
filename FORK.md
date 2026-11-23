# Fork ASSE03/bare-browser

Fork personnel de [BareBrowser/bare-browser](https://github.com/BareBrowser/bare-browser).
Il ajoute des patchs par-dessus la série d'origine, sans la modifier.

## Patchs ajoutés

Ils sont numérotés à partir de `9000001`, pour s'appliquer toujours après ceux de Bare
(`git apply` les prend dans l'ordre des noms de fichiers) et ne jamais entrer en
collision avec un numéro que Bare utilisera plus tard.

| Patch | Effet |
| --- | --- |
| `9000001.patch` | Action « Favoris » pour la barre d'outils : ouvre directement le dossier « Barre de favoris ». À choisir dans Paramètres › Barre d'outils ; en mode minimal, la première position est le bouton à gauche de la barre d'adresse. |
| `9000002.patch` | Option « Clear when swiped from recent apps » dans Confidentialité › Clear on exit : balayer Bare hors du multitâche efface ce qui est coché. Si Android tue Bare avant la fin, l'effacement se termine à l'ouverture suivante, avant l'affichage de toute page. |
| `9000003.patch` | Supprime deux messages en bas d'écran : « Onglet … fermé / Annuler » (la fermeture est validée tout de suite) et la notice d'entrée en plein écran (« Pour quitter le plein écran, faites glisser… »). |
| `9000004.patch` | Traduction française des textes de Bare : ses écrans (réglages, sauvegarde, accueil, barre d'outils…) et les textes de Chromium que Bare modifie, qui perdaient leur traduction. S'affiche quand le téléphone est en français. |
| `9000005.patch` | Ouvrir un favori depuis l'écran des favoris n'affiche plus brièvement le contenu précédent de l'onglet (site d'avant ou racine des favoris) : l'onglet affiche le dossier de favoris jusqu'au premier affichage du site (quelques secondes au maximum). |
| `9000006.patch` | Les favoris s'ouvrent dans l'onglet courant, sous la barre d'adresse, au lieu d'un écran séparé. Retour revient à la page d'avant. |
| `9000007.patch` | Une page d'accueil Favoris (au démarrage ou après le nettoyage) s'ouvre directement sur le dossier Barre de favoris, dans l'onglet ouvert. |
| `9000008.patch` | Un lien ouvert depuis une autre appli (mail…) alors que Bare avait été balayé des applis récentes s'affiche : le nettoyage ferme les anciens onglets mais garde celui du lien, sans ouvrir la page d'accueil. |

## Vérification automatique

Le workflow `Check patches` (onglet Actions) applique toute la série sur le Chromium
épinglé, sans rien compiler. Il tourne à chaque modification de `patches/`, tous les
matins, et à la demande.

- **fork** : la série de ce dépôt telle quelle.
- **upstream** : la dernière version de Bare, plus les patchs propres à ce fork. S'il
  échoue, synchroniser le fork cassera un de nos patchs : il faudra l'adapter avant.

En local : `python3 tools/check_patches.py`

## Mettre à jour depuis Bare

1. Vérifier que le job **upstream** est vert.
2. Sur GitHub : **Sync fork** › **Update branch**.
3. Compiler comme indiqué dans `BUILDING.md` (`git apply --index patches/*.patch` applique
   aussi les patchs de ce fork).
