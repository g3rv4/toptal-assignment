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
                        controller: 'SettingsCtrl as ctrl',
                        templateUrl: '/static/templates/control-panel/settings.html'
                    });

                $urlRouterProvider.when('', '/meals');
                $urlRouterProvider.otherwise('/meals');
            };
            return ['$stateProvider', '$urlRouterProvider', ControlPanelRouter];
        }
    );
}(define));