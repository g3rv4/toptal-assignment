(function (define) {
    define(
        [
            'angular',
            'controllers/control-panel/BaseController',
            'controllers/control-panel/MealsController',
            'services/ModelService',
            'services/RolesService',
            'routers/ControlPanelRouter',
            'ng-ui-router',
            'ng-resource',
            'ng-local-storage'
        ],
        function (ng, BaseCtrl, MealsCtrl, ModelService, RolesService, ControlPanelRouter) {
            var moduleName = 'Demo.ControlPanelModule';

            ng.module(moduleName, ['ui.router', 'ngResource', 'LocalStorageModule'])
                .controller('BaseCtrl', BaseCtrl)
                .controller('MealsCtrl', MealsCtrl)
                .factory('ModelService', ModelService)
                .factory('RolesService', RolesService)
                .config(ControlPanelRouter)
                .config(['localStorageServiceProvider', function(localStorageServiceProvider){
                    localStorageServiceProvider.setStorageType('sessionStorage');
                }])
                .config(['$httpProvider', function($httpProvider){
                    $httpProvider.interceptors.push(['$q', '$window', 'localStorageService', function ($q, $window, localStorageService) {
                        return {
                            'responseError': function (response) {
                                if (response.status == 401) {
                                    localStorageService.remove('roles');
                                    localStorageService.remove('access_token');
                                    $window.location.href = '/';
                                }
                                return $q.reject(response);
                            }
                        };
                    }]);
                }])
                .run(['$window', 'localStorageService', '$http', '$rootScope', function($window, localStorageService, $http, $rootScope){
                    var verify_token = function(){
                        if (!localStorageService.get('access_token')){
                            $window.location.href = '/';
                        }
                    };
                    $rootScope.$on('$stateChangeSuccess', function(){
                        verify_token();
                    });
                    verify_token();

                    $http.defaults.headers.common.Authorization = 'Bearer ' + localStorageService.get('access_token')
                }]);

            return moduleName;
        }
    )
}(define));