(function (define) {
    define(
        ['angular', 'controllers/public/LoginController', 'routers/PublicRouter', 'ng-ui-router'],
        function (ng, LoginController, PublicRouter) {
            var moduleName = 'Demo.PublicModule';

            ng.module(moduleName, ['ui.router'])
                .controller('LoginController', LoginController)
                .config(PublicRouter);

            return moduleName;
        }
    )
}(define));