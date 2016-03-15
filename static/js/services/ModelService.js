(function (define) {
    define([], function () {
        var ModelService = function ($resource) {

            var ModelFactory = function (name, url) {
                return $resource(url, {'id': '@id'}, {
                    update: {
                        method: 'PUT'
                    },
                    query: {
                        isArray: true,
                        transformResponse: function (data, headers) {
                            var data = JSON.parse(data);
                            if (Object.prototype.toString.call(data) === '[object Array]') {
                                return data
                            }

                            headers()['count'] = data.count;
                            return data.results;
                        }
                    }
                });
            };

            return {
                Account: ModelFactory('Account', '/api/accounts/:id')
            };
        };

        return ['$resource', ModelService];
    });
}(define));