class SearchResults(object):
    def __init__(self, results_dict):
        self.lots = {
            'IaaS': 'Infrastructure as a Service',
            'SaaS': 'Software as a Service',
            'PaaS': 'Platform as a Service',
            'SCS': 'Specialist Cloud Services'
        }
        self.total = results_dict['hits']['total']
        self.results = []
        results = results_dict['hits']['hits']
        for raw_result in results:
            result = {}
            for field in raw_result['fields']:
                result[field] = raw_result['fields'][field][0]

            result['lot'] = self.lots[result['lot']]
            self.results.append(result)

    def get_services(self):
        return self.results

    def get_total(self):
        return {'total': self.total}

    def get_results(self):
        return {
            'services': self.get_services(),
            'total': self.get_total()
        }
