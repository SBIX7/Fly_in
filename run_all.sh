#!/bin/bash

# Le fichier où tout sera enregistré
OUTPUT="resultats_globaux.txt"

# On vide le fichier s'il existait déjà pour repartir à zéro
> "$OUTPUT"

echo "🚀 Lancement de la batterie de tests..."

# On cherche tous les fichiers .txt dans le dossier maps, et on les trie
find ./maps -type f -name "*.txt" | sort | while read map_file; do
    
    echo "Vérification en cours : $map_file"
    
    echo "==================================================================" >> "$OUTPUT"
    echo "📍 CARTE : $map_file" >> "$OUTPUT"
    echo "==================================================================" >> "$OUTPUT"
    
    # 1. Ajout du contenu brut de la carte
    echo "--- CONTENU DE LA CARTE ---" >> "$OUTPUT"
    cat "$map_file" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    
    # 2. Ajout des résultats du simulateur
    echo "--- RÉSULTATS DE LA SIMULATION ---" >> "$OUTPUT"
    
    # On lance le script Python. 
    # On utilise 'sed' pour effacer dynamiquement tous les codes couleurs ANSI (les \033[...m)
    python main.py --map "$map_file" 2>&1 | sed $'s/\033\\[[0-9;]*m//g' >> "$OUTPUT"
    
    # On ajoute des sauts de ligne pour aérer la lecture entre chaque test
    echo -e "\n\n\n" >> "$OUTPUT"
    
done

echo "✅ Tous les tests sont terminés ! Les résultats propres sont dans le fichier '$OUTPUT'."
