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
                    })
                    .state('public.apply_account_changes', {
                        url: '/apply-account-changes?account_id&token',
                        controller: 'ApplyAccountChangesCtrl as ctrl',
                        templateUrl: '/static/templates/public/apply-account-changes.html'
                    });

                $urlRouterProvider.when('', '/login');
                $urlRouterProvider.otherwise('/login');
            };
            return ['$stateProvider', '$urlRouterProvider', PublicRouter];
        }
    );
}(define));