(function (define) {
    define(
        [],
        function () {
            var EqualsDirective = function () {
                // from http://stackoverflow.com/a/18014975/920295
                return {
                    restrict: 'A', // only activate on element attribute
                    require: '?ngModel', // get a hold of NgModelController
                    link: function (scope, elem, attrs, ngModel) {
                        if (!ngModel) return; // do nothing if no ng-model

                        // watch own value and re-validate on change
                        scope.$watch(attrs.ngModel, function () {
                            validate();
                        });

                        // observe the other value and re-validate on change
                        attrs.$observe('equals', function (val) {
                            validate();
                        });

                        var validate = function () {
                            // values
                            var val1 = ngModel.$viewValue;
                            var val2 = attrs.equals;

                            // set validity
                            ngModel.$setValidity('equals', !val2 || val1 === val2);
                        };
                    }
                }
            };

            return [EqualsDirective];
        }
    );
}(define));