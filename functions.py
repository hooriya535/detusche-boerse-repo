import requests  
import json  
import logging  
  
logger = logging.getLogger(__name__)
  
def search_etfs(query='', entries=10, sort='{"shareClassVolume": "desc"}'):  
    logger.info(f"Searching ETFs with query: '{query}', entries: {entries}, sort: {sort}")  
  
    # Parse the sort parameter from JSON string to dictionary  
    try:  
        sort = json.loads(sort)  
        logger.info(f"Parsed sort parameter: {sort}")  
    except json.JSONDecodeError as e:  
        logger.error(f"Error parsing sort parameter: {e}")  
        sort = {"shareClassVolume": "desc"}  
        logger.info("Using default sort parameter.")  
    
    page = 1  
    filter = {}  
      
    url = 'https://search.finanzfluss.de/graphql'  
    graphql_query = """  
            fragment CoreSearchFields on SearchResult2 {  
                aggregations  
                total  
                unfilteredTotal  
                pages  
                currentPage  
                currentPer  
                __typename  
            }  
    
            fragment OverviewTableFields on ETF {  
                releaseDate  
                fundVolume  
                shareClassVolume  
                totalExpenseRatio  
                isDistributing  
                replicationMethod  
                currency  
                preferredPerformanceIdId  
                __typename  
            }  
    
            query InformerSearchQuery($query: String, $per: Int, $page: Int, $filter: JSON, $sort: JSON) {  
                search(q: $query, per: $per, page: $page, filter: $filter, sort: $sort) {  
                    ...CoreSearchFields  
                    results {  
                        isin  
                        name  
                        displayName  
                        preferredPerformanceIdId  
                        ...OverviewTableFields  
                        __typename  
                    }  
                    __typename  
                }  
            }  
        """  
      
    variables = {  
        'query': query,  
        'per': entries,  
        'page': page,  
        'filter': filter,  
        'sort': sort  
    }  
      
    headers = {  
        'Content-Type': 'application/json; charset=utf-8'  
    }  
      
    try:  
        response = requests.post(url, headers=headers, json={  
            'operationName': 'InformerSearchQuery',  
            'query': graphql_query,  
            'variables': variables  
        })  
  
        if response.status_code == 200:  
            data = response.json()  
            search_data = data['data']['search']  
  
            search_results = {  
                'aggregations': search_data.get('aggregations', {}),  
                'total': search_data.get('total', 0),  
                'pages': search_data.get('pages', 0),  
                'currentPage': search_data.get('currentPage', 0),  
                'currentPer': search_data.get('currentPer', 0),  
                'results': [result for result in search_data.get('results', [])]  
            }  
            logger.info(f"ETF search successful. Total results found: {search_data.get('total', 0)}")  
            return json.dumps(search_results, indent=4)  
        else:  
            logger.error(f"ETF search failed with status code: {response.status_code}")  
            response.raise_for_status()  
    except requests.RequestException as e:  
        logger.exception(f"An error occurred during ETF search: {e}", exc_info=True)  
        raise 
