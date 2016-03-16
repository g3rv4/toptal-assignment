(function (define) {
    define(
        [],
        function () {
            var BaseController = function (localStorageService, RolesService, $window) {
                var _this = this;

                _this.userHasRole = RolesService().userHasRole;

                _this.logout = function(){
                    localStorageService.clearAll();
                    $window.location.href = '/';
                };
            };

            return ['localStorageService', 'RolesService', '$window', BaseController];
        }
    );
}(define));