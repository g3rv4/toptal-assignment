(function (define) {
    define(
        ['lodash'],
        function (_) {
            var LoginController = function ($http, $httpParamSerializerJQLike, localStorageService, $window) {
                var _this = this;
                _this.form = {};

                _this.submit = function(){
                    _this.form.sent = true;

                    if(_this.formElement.$valid) {
                        $http.post('/api/oauth', $httpParamSerializerJQLike({
                            grant_type: 'password',
                            username: _this.form.email,
                            password: _this.form.password
                        }), {
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                        }).then(function(response){
                            localStorageService.set('roles', _.split(response.data.scope, ' '));
                            localStorageService.set('access_token', response.data.access_token);
                            $window.location.href = '/control-panel/';
                        }, function(response){
                            if(response.data.error){
                                if(response.data.error_description){
                                    _this.error_message = response.data.error_description;
                                } else if(response.data.error == 'invalid_grant') {
                                    _this.error_message = 'Invalid email or password';
                                } else {
                                    _this.error_message = 'Error logging in. Code: ' + response.data.error;
                                }
                            } else {
                                _this.error_message = 'Unexpected error ' + response.status;
                            }
                        })
                    }
                };
            };

            return ['$http', '$httpParamSerializerJQLike', 'localStorageService', '$window', LoginController];
        }
    );
}(define));