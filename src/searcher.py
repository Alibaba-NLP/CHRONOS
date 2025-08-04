import os
import json
import requests
import concurrent.futures
import logging
from typing import Dict, List

BING_SEARCH_KEY =  "YOUR_API_KEY"

def search(query_list: List[str], n_max_doc: int = 20, search_engine: str = 'bing', freshness: str = '') -> List[Dict[str, str]]:
    doc_lists = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_single, query, search_engine, freshness) for query in query_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                doc_lists.append(future.result())
            except:
                pass
    doc_list = _rearrange_and_dedup([d for d in doc_lists if d])
    return doc_list[:n_max_doc]


def search_single(query: str, search_engine: str, freshness: str = '') -> List[Dict[str, str]]:
    try:
        if search_engine == 'bing':
            search_results = bing_request(query, freshness=freshness)
            return bing_format_results(search_results)
        else:
            raise ValueError(f'Unsupported Search Engine: {search_engine}')
    except Exception as e:
        logging.error(f'Search failed: {str(e)}')
        raise ValueError(f'Search failed: {str(e)}')


def bing_request(query: str, count: int = 50, freshness: str = '') -> List[Dict[str, str]]:
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {'Ocp-Apim-Subscription-Key': BING_SEARCH_KEY}
    params = {'q': query, 'count': count, 'responseFilter': 'Webpages', 'freshness': f'1900-01-01..{freshness}'}
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        web_pages = data.get('webPages', {}).get('value', [])
        return web_pages

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  
    except Exception as err:
        print(f"An error occurred: {err}")  

    return []


def bing_format_results(search_results: List[Dict[str, str]]):
    formatted_results = [
        {
            'id': str(rank + 1),
            'title': str(res.get('name', '')),
            'snippet': str(res.get('snippet', '')),
            'url': str(res.get('url', '')),
            'timestamp': str(res.get('dateLastCrawled', ''))[:10]
        }
        for rank, res in enumerate(search_results)
    ]
    return formatted_results


def _rearrange_and_dedup(doc_lists: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    doc_list = []
    snippet_set = set()
    # print([len(i) for i in doc_lists])
    for i in range(50):
        for ds in doc_lists:
            if i < len(ds):
                if 'snippet' in ds[i]:
                    signature = ds[i]['snippet'].replace(' ', '')[:200]
                else:
                    signature = ds[i]['content'].replace(' ', '')[:200]
                if signature not in snippet_set:
                    doc_list.append(ds[i])
                    snippet_set.add(signature)
    return doc_list


if __name__ == '__main__':
    queries = ["egypt crisis timeline"]
    from pprint import pprint
    pprint(search(queries, search_engine='bing', n_max_doc=30))
