(function(define) {
    define(
        ['angular', 'modules/PublicModule'],
        function (ng, PublicModule) {
            var app, appName = 'Demo';

            app = ng.module(appName, [PublicModule])
                .config(['$locationProvider', function($locationProvider){
                    $locationProvider.html5Mode(true);
                }]);

            ng.bootstrap(ng.element(document.getElementsByTagName("body")[0]), [appName]);

            return app;
        }
    );
}(define));
