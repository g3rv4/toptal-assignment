(function (define) {
    define(
        [],
        function () {
            var ControlPanelRouter = function ($stateProvider, $urlRouterProvider) {
                $stateProvider
                    .state('controlpanel', {
                        abstract: true,
                        controller: 'BaseCtrl as ctrl',
                        templateUrl: '/static/templates/control-panel/base.html'
                    })
                    .state('controlpanel.index', {
                        url: '/',
                        template: ''
                    })
                    .state('controlpanel.meals', {
                        url: '/meals',
                        controller: 'MealsCtrl as ctrl',
                        templateUrl: '/static/templates/control-panel/meals.html'
                    })
                    .state('controlpanel.settings', {
                        url: '/settings',
                        controller: 'SettingsCtrl as ctrl',
                        templateUrl: '/static/templates/control-panel/settings.html'
                    })
                    .state('controlpanel.users', {
                        url: '/users',
                        controller: 'UsersCtrl as ctrl',
                        templateUrl: '/static/templates/control-panel/users.html'
                    })
                    .state('controlpanel.users.edit', {
                        url: '/:user_id',
                        views: {
                            meals: {
                                controller: 'MealsCtrl as ctrl',
                                templateUrl: '/static/templates/control-panel/meals.html'
                            }
                        }
                    });

                $urlRouterProvider.otherwise('/');
            };
            return ['$stateProvider', '$urlRouterProvider', ControlPanelRouter];
        }
    );
}(define));