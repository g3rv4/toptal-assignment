(function (define) {
    define(
        [],
        function () {
            var DeleteMealController = function ($uibModalInstance, meal) {
                var _this = this;
                _this.meal = meal;

                _this.ok = function(){
                    $uibModalInstance.close();
                };

                _this.cancel = function(){
                    $uibModalInstance.dismiss('cancel');
                };
            };

            return ['$uibModalInstance', 'meal', DeleteMealController];
        }
    );
}(define));