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
                        controller: 'LoginCtrl as ctrl',
                        templateUrl: '/static/templates/public/login.html'
                    })
                    .state('public.register', {
                        url: '/register',
                        controller: 'RegisterCtrl as ctrl',
                        templateUrl: '/static/templates/public/register.html'
                    });

                $urlRouterProvider.when('', '/login');
                $urlRouterProvider.otherwise('/login');
            };
            return ['$stateProvider', '$urlRouterProvider', PublicRouter];
        }
    );
}(define));