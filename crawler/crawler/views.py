import os

from django.shortcuts import render
import json

from elasticsearch import Elasticsearch

from crawler.settings import BASE_DIR

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

with open(os.path.join(BASE_DIR, "crawler", "x.json"), "r") as f:
    clusters = json.loads(f.read())
with open(os.path.join(BASE_DIR, "crawler", "pr.json"), "r") as f:
    page_rank = json.loads(f.read())


def home(request):
    return render(request, 'home.html', {

    })


def search(request):
    q = request.GET.get('search')
    tw = request.GET.get('tweight') or 1
    kw = request.GET.get('kweight') or 1
    aw = request.GET.get('aweight') or 1
    hits = es.search(index="rg", body={
        "query": {
            "bool": {
                "should": [
                    {"match": {
                        "title": {
                            "query": q,
                            "boost": tw
                        }}},
                    {"match": {
                        "abstract": {
                            "query": q,
                            "boost": kw
                        }}},
                    {"match": {
                        "author": {
                            "query": q,
                            "boost": aw
                        }}},
                ]
            },
        },
        "_source": False,
        "fields": ["title", "abstract", "author", "id", "link"]
    })
    hits = hits.get('hits').get('hits')
    selected_clusters = request.GET.getlist('cluster')
    selected_clusters_docs = []
    for y in selected_clusters:
        selected_clusters_docs.extend(clusters[y][0])
    for h in hits:
        h.update({'score': h.get('_score')})
    final_hits = []
    for h in hits:
        doc_id = h.get('fields', {}).get('id')[0]
        if not selected_clusters or doc_id in selected_clusters_docs:
            ix = page_rank['map'][str(doc_id)][1]
            h.update({'page_rank': page_rank['rank'][0][ix]})
            final_hits.append(h)
    return render(request, 'result.html', {
        'title': q,
        'hits': final_hits,
        'tw': tw,
        'kw': kw,
        'aw': aw,
        'clusters': clusters
    })
