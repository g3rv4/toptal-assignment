(function (define) {
    define(
        [],
        function () {
            var AddHasErrorClass = function ($timeout) {
                // from http://stackoverflow.com/a/21739917/920295
                return {
                    restrict: "A",
                    link: function (scope, element, attrs, ctrl) {
                        var input = element.find('input[ng-model]');
                        if (input.length) {
                            $timeout(function(){
                                scope.$watch(function () {
                                    return input.controller('ngModel').$invalid;
                                }, function (isInvalid) {
                                    element.toggleClass('has-error', isInvalid);
                                });
                            }, 500);
                        }
                    }
                };
            };

            return ['$timeout', AddHasErrorClass];
        }
    );
}(define));