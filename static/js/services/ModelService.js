(function (define) {
    define(['lodash'], function (_) {
        var ModelService = function ($resource) {

            var ModelFactory = function (name, url) {
                return $resource(url, {'id': '@id'}, {
                    update: {
                        method: 'PUT'
                    },
                    query: {
                        isArray: true,
                        transformResponse: function (data, headers, status_code) {
                            if(status_code.toString().charAt(0) != 2){
                                try{
                                    data = JSON.parse(data)
                                } catch(e) { }
                                return data;
                            }
                            var data = JSON.parse(data);
                            data.data = _.map(data.data, function(item){
                                if(item.id && !_.isNumber(item.id)){
                                    item.id = parseInt(_.last(_.split(item.id, '/')))
                                }
                                return item;
                            });
                            headers()['count'] = data.pagination.total_items;
                            return data.data;
                        }
                    }
                });
            };

            return {
                Account: ModelFactory('Account', '/api/accounts/:id'),
                Meal: function (account_id) {
                    return ModelFactory('Meal', '/api/accounts/' + (account_id || 0) + '/meals/:id')
                }
            };
        };

        return ['$resource', ModelService];
    });
}(define));
