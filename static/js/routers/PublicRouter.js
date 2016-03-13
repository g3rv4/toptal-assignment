(function (define) {
    define(
        [],
        function () {
            var PublicRouter = function ($stateProvider, $urlRouterProvider) {
                $stateProvider
                    .state('public', {
                        abstract: true,
                        templateUrl: '/static/templates/public/base.html'
                    })
                    .state('public.login', {
                        url: '/login',
                        templateUrl: '/static/templates/public/login.html'
                    });

                $urlRouterProvider.when('', '/login');
                $urlRouterProvider.otherwise('/login');
            };
            return ['$stateProvider', '$urlRouterProvider', PublicRouter];
        }
    );
}(define));