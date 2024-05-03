import requests  
import json  
  
def search_etfs(query=''):  
    # Set default values for other parameters inside the function  
    per = 25  
    page = 1  
    filter = {}  
    sort = {'shareClassVolume': 'desc'}  
      
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
        'per': per,  
        'page': page,  
        'filter': filter,  
        'sort': sort  
    }  
      
    headers = {  
        'Content-Type': 'application/json; charset=utf-8'  
    }  
      
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
        return json.dumps(search_results, indent=4)  
    else:  
        response.raise_for_status()  
