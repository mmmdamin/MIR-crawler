import json
import os
from time import sleep

import requests
import sys
from tqdm import tqdm

yellow_color = "\033[93m"
red_color = "\033[91m"
articles_path = "../crawler/articles"
elastic_search_url = "http://localhost:9200/rg/article/{}"

for article_name in tqdm(os.listdir(articles_path), desc=yellow_color + "Indexing", file=sys.stdout):
    with open(os.path.join(articles_path, article_name), 'r') as f:
        x = f.read()
        article = json.loads(x)
        r = requests.put(elastic_search_url.format(article.get('id')), x, headers={
            'Content-Type': 'application/json'
        })
        sleep(0.3)
print(red_color + "Indexing finished!")
