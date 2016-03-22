(function (define) {
    define(
        ['angular', 'lodash'],
        function (angular, _) {
            var UsersController = function (ModelService, RolesService, $uibModal, $state, $rootScope, $timeout) {
                var _this = this;
                var User = ModelService['Account'];

                _this.datepickerOptions = {
                    showWeeks: false,
                    maxDate: Date()
                };
                _this.datepickersOpen = {};
                _this.query = {'items-per-page': 5, page: 1};
                _this.newUser = {};
                _this.addUserAlerts = [];
                _this.usersAlerts = [];
                _this.totalItems = 0;
                _this.filtersVisible = false;
                _this.addUserVisible = true;
                _this.userHasRole = RolesService().userHasRole;

                var updateEditingUser = function(user_id){
                    _this.showMeals = 0;
                    _this.editFormSent = false;
                    _this.editingRoles = {};
                    User.get({id: user_id}, function(user){
                        _this.editingUser = user;
                        _this.editingRoles = {
                            'user': user.roles.indexOf('user') != -1,
                            'userManager': user.roles.indexOf('user-manager') != -1,
                            'admin': user.roles.indexOf('admin') != -1
                        };
                    });
                };

                $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams){
                    if(toState.name == 'controlpanel.users'){
                        _this.editingUser = null;
                        $timeout(function(){
                            _this.refreshData();
                        }, 500);
                    } else if(toState.name == 'controlpanel.users.edit'){
                        updateEditingUser(toParams.user_id);
                    }
                });
                if($state.params.user_id){
                    updateEditingUser($state.params.user_id);
                }

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

                    if(!_this.query.name){
                        delete realQuery.name;
                    }
                    if(!_this.query.email){
                        delete realQuery.email;
                    }

                    User.query(realQuery, function(res, headers){
                        _this.elements = res;
                        _this.totalItems = headers()['count'];
                    }, function(response){
                        if(response.data.error){
                            _this.usersAlerts.push({
                                message: response.data.error
                            });
                        } else {
                            _this.usersAlerts.push({
                                message: 'Unexpected error ' + response.status
                            });
                        }
                    });
                };

                _this.printableRoles = function(roles){
                    return _.join(roles, ', ');
                };

                _this.addUser = function(){
                    _this.userFormSent = true;

                    if(_this.formElement.$valid){
                        var user = new User(_this.newUser);
                        user.$save(function(){
                            _this.newUser = {};
                            _this.userFormSent = false;
                            _this.addUserAlerts.push({
                                type: 'success',
                                message: 'User successfully added. An email has been sent for them to activate their account'
                            });
                            _this.refreshData();
                        }, function(response){
                            if(response.data.error){
                                _this.addUserAlerts.push({
                                    message: response.data.error
                                });
                            } else {
                                _this.addUserAlerts.push({
                                    message: 'Unexpected error ' + response.status
                                });
                            }
                            _this.success = false;
                        });
                    }
                };

                _this.editUser = function(){
                    _this.editFormSent = true;

                    if(_this.formEditElement.$valid){
                        _this.editingUser.roles = [];
                        _.forOwn(_this.editingRoles, function(v, k){
                            if(v){
                                k = k == 'userManager' ? 'user-manager' : k;
                                _this.editingUser.roles.push(k);
                            }
                        });
                        _this.editingUser.$update(function(){
                            _this.usersAlerts.push({
                                type: 'success',
                                message: 'User ' + _this.editingUser.id + ' updated successfully'
                            });
                            $state.go('controlpanel.users');
                        }, function(response){
                            if(response.data.error){
                                _this.usersAlerts.push({
                                    message: response.data.error
                                });
                            } else {
                                _this.usersAlerts.push({
                                    message: 'Unexpected error ' + response.status
                                });
                            }
                            _this.success = false;
                        });
                    }
                };

                _this.deleteUser = function(user){
                    var modal = $uibModal.open({
                        templateUrl: '/static/templates/control-panel/modal/delete-user.html',
                        controller: 'DeleteItemCtrl',
                        controllerAs: 'ctrl',
                        resolve: {
                            item: function(){
                                return user;
                            }
                        }
                    });

                    modal.result.then(function(){
                        user.$delete(function(){
                            _this.usersAlerts.push({
                                type: 'success',
                                message: 'User ' + user.id + ' deleted successfully'
                            });
                            _this.refreshData();
                        }, function(response){
                            if(response.data.error){
                                _this.usersAlerts.push({
                                    message: response.data.error
                                });
                            } else {
                                _this.usersAlerts.push({
                                    message: 'Unexpected error ' + response.status
                                });
                            }
                            _this.success = false;
                        });
                    })
                };

                _this.refreshData();
            };

            return ['ModelService', 'RolesService', '$uibModal', '$state', '$rootScope', '$timeout', UsersController];
        }
    );
}(define));