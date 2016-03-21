(function(define) {
    define(
        ['angular', 'modules/ControlPanelModule'],
        function (ng, ControlPanelModule) {
            var app, appName = 'Demo';

            app = ng.module(appName, [ControlPanelModule])
                .config(['$locationProvider', function($locationProvider){
                    $locationProvider.html5Mode(true);
                }]);

            ng.bootstrap(ng.element(document.getElementsByTagName("body")[0]), [appName]);

            return app;
        }
    );
}(define));