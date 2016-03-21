(function (define) {
    define(
        ['angular', 'moment'],
        function (angular, moment) {
            var MealsController = function (ModelService, $uibModal) {
                var _this = this;
                var Meal = ModelService['Meal'](0);

                _this.datepickerOptions = {
                    showWeeks: false,
                    maxDate: Date()
                };
                _this.datepickersOpen = {};
                _this.query = {'items-per-page': 5, page: 1};
                _this.newMeal = {};
                _this.addMealAlerts = [];
                _this.mealsAlerts = [];
                _this.totalItems = 0;
                _this.filtersVisible = false;
                _this.addMealVisible = true;

                _this.openDatepicker = function(name){
                    _this.datepickersOpen[name] = true;
                };

                _this.doFilter = function(){
                    _this.query.page = 1;
                    _this.refreshData();
                };

                _this.setItemsPerPage = function(pageSize){
                    _this.query['items-per-page'] = pageSize;
                    _this.query.page = 1;
                    _this.refreshData();
                };

                _this.resetQuery = function(){
                    _this.query = {'items-per-page': 5, page: 1};
                    _this.refreshData();
                };

                _this.refreshData = function(){
                    var realQuery = angular.copy(_this.query);

                    // update the parameter formats to match the API
                    if(realQuery.hasOwnProperty('mealDateFrom') && realQuery.mealDateFrom) {
                        realQuery['meal-date-from'] = moment(realQuery.mealDateFrom).format('YYYY-MM-DD');
                        delete realQuery.mealDateFrom;
                    }
                    if(realQuery.hasOwnProperty('mealDateTo') && realQuery.mealDateTo) {
                        realQuery['meal-date-to'] = moment(realQuery.mealDateTo).format('YYYY-MM-DD');
                        delete realQuery.mealDateTo;
                    }
                    if(realQuery.hasOwnProperty('mealTimeFrom') && realQuery.mealTimeFrom) {
                        realQuery['meal-time-from'] = moment(realQuery.mealTimeFrom).format('HH:mm:ss');
                        delete realQuery.mealTimeFrom;
                    }
                    if(realQuery.hasOwnProperty('mealTimeTo') && realQuery.mealTimeTo) {
                        realQuery['meal-time-to'] = moment(realQuery.mealTimeTo).format('HH:mm:ss');
                        delete realQuery.mealTimeTo;
                    }

                    Meal.query(realQuery, function(res, headers){
                        _this.elements = res;
                        _this.totalItems = headers()['count'];
                    }, function(response){
                        if(response.data.error){
                            _this.mealsAlerts.push({
                                message: response.data.error
                            });
                        } else {
                            _this.mealsAlerts.push({
                                message: 'Unexpected error ' + response.status
                            });
                        }
                    });
                };

                _this.addMeal = function(){
                    _this.mealFormSent = true;

                    if(_this.formElement.$valid){
                        var realMeal = angular.copy(_this.newMeal);
                        realMeal.date = moment(_this.newMeal.date).format('YYYY-MM-DD');
                        realMeal.time = moment(_this.newMeal.time).format('HH:mm:ss');
                        var meal = new Meal(realMeal);
                        meal.$save(function(){
                            _this.newMeal = {};
                            _this.mealFormSent = false;
                            _this.addMealAlerts.push({
                                type: 'success',
                                message: 'Meal successfully added'
                            });
                            _this.refreshData();
                        }, function(response){
                            if(response.data.error){
                                _this.addMealAlerts.push({
                                    message: response.data.error
                                });
                            } else {
                                _this.addMealAlerts.push({
                                    message: 'Unexpected error ' + response.status
                                });
                            }
                            _this.success = false;
                        });
                    }
                };

                _this.editMeal = function(meal){
                    var modal = $uibModal.open({
                        templateUrl: '/static/templates/control-panel/modal/edit-meal.html',
                        controller: 'EditMealCtrl',
                        controllerAs: 'ctrl',
                        resolve: {
                            meal: function(){
                                return meal;
                            }
                        }
                    });

                    modal.result.then(function(){
                        _this.refreshData();
                    })
                };

                _this.deleteMeal = function(meal){
                    var modal = $uibModal.open({
                        templateUrl: '/static/templates/control-panel/modal/delete-meal.html',
                        controller: 'DeleteMealCtrl',
                        controllerAs: 'ctrl',
                        resolve: {
                            meal: function(){
                                return meal;
                            }
                        }
                    });

                    modal.result.then(function(){
                        meal.$delete(function(){
                            _this.refreshData();
                        }, function(response){
                            if(response.data.error){
                                _this.mealsAlerts.push({
                                    message: response.data.error
                                });
                            } else {
                                _this.mealsAlerts.push({
                                    message: 'Unexpected error ' + response.status
                                });
                            }
                            _this.success = false;
                        });
                    })
                };

                _this.refreshData();
            };

            return ['ModelService', '$uibModal', MealsController];
        }
    );
}(define));