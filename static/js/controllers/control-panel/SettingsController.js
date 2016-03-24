(function (define) {
    define(
        ['lodash', 'moment'],
        function (_, moment) {
            var SettingsController = function (ModelService, $scope, RolesService) {
                var _this = this;
                var User = ModelService.Account;
                var Meal = ModelService.Meal(0);

                _this.alerts = [];
                _this.caloriesDay = new Date();
                _this.lastMealsQuery = null;
                _this.datepickerOptions = {
                    maxDate: new Date(),
                    showWeeks: false
                };
                _this.userHasRole = RolesService().userHasRole;


                var updateUser = function (resetForm) {
                    User.get({id: 0}, function (user) {
                        _this.user = user;
                        if (resetForm) {
                            _this.form = _.pick(user, ['name', 'email', 'calories_goal']);
                        }
                        _this.updateCaloriesCount();
                    });
                };

                _this.updateSettings = function () {
                    _.forOwn(_this.form, function (v, k) {
                        _this.user[k] = v;
                    });
                    _this.user.$update(function () {
                        _this.alerts.push({
                            type: 'success',
                            message: 'Account updated successfully'
                        });
                        updateUser(true);
                        _this.changePassword = false;
                    }, function (response) {
                        updateUser();
                        if (response.data.error) {
                            _this.alerts.push({
                                message: response.data.error
                            });
                        } else {
                            _this.alerts.push({
                                message: 'Unexpected error ' + response.status
                            });
                        }
                    })
                };

                _this.updateCaloriesCount = function(){
                    if(_this.userHasRole('user') &&_this.caloriesDay != _this.lastMealsQuery) {
                        _this.lastMealsQuery = _this.caloriesDay;

                        Meal.query({
                            'meal-date-from': moment(_this.caloriesDay).format('YYYY-MM-DD'),
                            'meal-date-to': moment(_this.caloriesDay).format('YYYY-MM-DD')
                        }, function (meals) {
                            _this.calories = _.sumBy(meals, function(m){ return m.calories; });
                            _this.caloriesDayStr = moment(_this.caloriesDay).format('M/D');
                        });
                    }
                };

                $scope.$watch(function(){
                    return _this.caloriesDay;
                }, function(){
                    _this.updateCaloriesCount()
                });

                updateUser(true);
            };

            return ['ModelService', '$scope', 'RolesService', SettingsController];
        }
    );
}(define));