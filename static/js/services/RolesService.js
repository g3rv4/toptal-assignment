(function (define) {
    define([], function () {
        var RolesService = function (localStorageService) {

            return function(){
                return {
                    userHasRole: function(requiredRole){
                        var userRoles = localStorageService.get('roles');
                        if(userRoles)
                            return userRoles.indexOf(requiredRole) != -1;
                        return false;
                    }
                }
            };
        };

        return ['localStorageService', RolesService];
    });
}(define));