(function (define) {
    define(
        [],
        function () {
            var BaseController = function (localStorageService, RolesService, $window, $state) {
                var _this = this;

                _this.userHasRole = RolesService().userHasRole;

                var needsChange = $state.is('controlpanel.index') ||
                    ($state.is('controlpanel.meals') && !_this.userHasRole('user')) ||
                    ($state.is('controlpanel.users') && !_this.userHasRole('admin') && !_this.userHasRole('user-manager'));

                if(needsChange) {
                    if (_this.userHasRole('admin') || _this.userHasRole('user-manager')) {
                        $state.go('controlpanel.users');
                    } else if (_this.userHasRole('user')) {
                        $state.go('controlpanel.meals');
                    } else {
                        $state.go('controlpanel.settings');
                    }
                }

                _this.logout = function(){
                    localStorageService.clearAll();
                    $window.location.href = '/';
                };
            };

            return ['localStorageService', 'RolesService', '$window', '$state', BaseController];
        }
    );
}(define));