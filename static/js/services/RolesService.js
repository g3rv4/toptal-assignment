(function (define) {
    define([], function () {
        var RolesService = function (localStorageService) {

            return function(){
                return {
                    userHasRole: function(requiredRole){
                        var userRoles = localStorageService.get('roles');
                        return userRoles.indexOf(requiredRole) != -1;
                    }
                }
            };
        };

        return ['localStorageService', RolesService];
    });
}(define));