import json
import os

import networkx as nx

articles_path = "articles"


def draw_graph():
    g = nx.DiGraph()
    for article_name in os.listdir(articles_path):
        with open(os.path.join(articles_path, article_name), 'r') as f:
            x = f.read()
            article = json.loads(x)
            article_id = article.get('id')
            article_cited_in = article.get('citedIn')
            article_reference = article.get('reference')

            g.add_node(article_id)
            g.add_nodes_from(article_cited_in)
            g.add_nodes_from(article_reference)

            for a in article_cited_in:
                g.add_edge(a, article_id)
            for a in article_reference:
                g.add_edge(article_id, a)

    nx.write_dot(g, 'graph.dot')
