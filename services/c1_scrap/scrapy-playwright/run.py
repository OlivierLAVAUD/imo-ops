#!/usr/bin/env python3
import os
import sys
from scrapy.cmdline import execute

def main():
    """Lance le spider avec des paramètres par défaut"""
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Paramètres par défaut
    localisation = "Montpellier"
    max_biens = 50
    
    # Récupérer les arguments de la ligne de commande
    if len(sys.argv) > 1:
        localisation = sys.argv[1]
    if len(sys.argv) > 2:
        max_biens = sys.argv[2]
    
    execute([
        'scrapy', 'crawl', 'iad_france',
        '-a', f'localisation={localisation}',
        '-a', f'max_biens={max_biens}',
        '-s', 'CONCURRENT_REQUESTS=1',
        '-s', 'DOWNLOAD_DELAY=2'
    ])

if __name__ == '__main__':
    main()