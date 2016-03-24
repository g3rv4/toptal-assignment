(function (define) {
    define(
        ['moment', 'angular'],
        function (moment, angular) {
            var EditMealController = function ($uibModalInstance, meal) {
                var _this = this;
                var mealDate = moment(meal.date + ' ' + meal.time).toDate();
                _this.meal = angular.copy(meal);
                _this.mealForm = {
                    date: mealDate,
                    time: mealDate
                };
                _this.datepickerOptions = {
                    showWeeks: false,
                    maxDate: Date()
                };

                _this.submit = function () {
                    _this.meal.date = moment(_this.mealForm.date).format('YYYY-MM-DD');
                    _this.meal.time = moment(_this.mealForm.time).format('HH:mm:ss');
                    _this.meal.$update(function () {
                        $uibModalInstance.close();
                    }, function (response) {
                        if (response.data.error) {
                            _this.error = response.data.error
                        } else {
                            _this.error = 'Unexpected error ' + response.status
                        }
                    });
                };

                _this.cancel = function () {
                    $uibModalInstance.dismiss('cancel');
                };
            };

            return ['$uibModalInstance', 'meal', EditMealController];
        }
    );
}(define));