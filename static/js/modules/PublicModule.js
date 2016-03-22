(function (define) {
    define(
        [
            'angular',
            'controllers/public/LoginController',
            'controllers/public/RegisterController',
            'controllers/public/ApplyAccountChangesController',
            'directives/EqualsDirective',
            'services/ModelService',
            'routers/PublicRouter',
            'ng-ui-router',
            'ng-resource',
            'ng-local-storage'
        ],
        function (ng, LoginCtrl, RegisterCtrl, ApplyAccountChangesCtrl, EqualsDirective, ModelService, PublicRouter) {
            var moduleName = 'Demo.PublicModule';

            ng.module(moduleName, ['ui.router', 'ngResource', 'LocalStorageModule'])
                .controller('LoginCtrl', LoginCtrl)
                .controller('RegisterCtrl', RegisterCtrl)
                .controller('ApplyAccountChangesCtrl', ApplyAccountChangesCtrl)
                .directive('equals', EqualsDirective)
                .factory('ModelService', ModelService)
                .config(PublicRouter)
                .config(['localStorageServiceProvider', function(localStorageServiceProvider){
                    localStorageServiceProvider.setStorageType('sessionStorage');
                }]);

            return moduleName;
        }
    )
}(define));