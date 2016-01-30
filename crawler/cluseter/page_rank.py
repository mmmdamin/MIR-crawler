import json
import math
import os
import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


def distance(v, u):
    sum = 0
    for i in range(v.size):
        sum += (v[0][i] - u[0][i]) * (v[0][i] - u[0][i])
    return math.sqrt(sum)


articles_path = '../crawler/articles'
articles = []
refrences = {}
for article_name in os.listdir(articles_path):
    try:
        article = es.get_source(index="rg", doc_type="article", id=int(article_name.split(".")[0]))
        articles.append(article)
        refrences[article['id']] = article.get('reference')
    except NotFoundError:
        pass
my_map = {}
for i, article in enumerate(articles):
    my_map[article['id']] = (article, i)
p = np.zeros((len(articles), len(articles)))
for i, a in enumerate(articles):
    for j, b in enumerate(refrences[a['id']]):
        if my_map.has_key(b):
            p[my_map[a['id']][1]][my_map[b][1]] = 1
# for i,j in range(len(articles),len(articles)):
#     print(p[i][j])
delta = 0.00001
for i in range(len(articles)):
    sum = 0
    for j in range(len(articles)):
        sum += p[i][j]
    for j in range(len(articles)):
        if sum == 0:
            p[i][j] = 1.0 / len(articles)
        else:
            p[i][j] /= sum
size = len(articles)
v = np.zeros((size, size))
v.fill(1.0 / size)
p = .9 * p + .1 * v
a1 = np.zeros((1, size))
a2 = np.zeros((1, size))
a1.fill(0)
a2.fill(1.0 / size)
while distance(a1, a2) > delta:
    a1 = a2
    a2 = a2.dot(p)

with open("../crawler/pr.json", "w") as f:
    f.write(json.dumps({'rank': a2.tolist(), 'map': my_map}))
