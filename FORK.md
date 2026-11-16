# Fork ASSE03/bare-browser

Fork personnel de [BareBrowser/bare-browser](https://github.com/BareBrowser/bare-browser).
Il ajoute des patchs par-dessus la série d'origine, sans la modifier.

## Patchs ajoutés

Ils sont numérotés à partir de `9000001`, pour s'appliquer toujours après ceux de Bare
(`git apply` les prend dans l'ordre des noms de fichiers) et ne jamais entrer en
collision avec un numéro que Bare utilisera plus tard.

| Patch | Effet |
| --- | --- |
| `9000001.patch` | Action « Favoris » pour la barre d'outils : ouvre la liste de tous les favoris. À choisir dans Paramètres › Barre d'outils ; en mode minimal, la première position est le bouton à gauche de la barre d'adresse. |
| `9000002.patch` | Option « Clear when swiped from recent apps » dans Confidentialité › Clear on exit : balayer Bare hors du multitâche efface ce qui est coché. Si Android tue Bare avant la fin, l'effacement se termine à l'ouverture suivante, avant l'affichage de toute page. |

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
