(function (define) {
    define(
        [],
        function () {
            var ApplyAccountChangesController = function ($stateParams, ModelService) {
                var _this = this;

                var Account = ModelService['Account'];
                new Account.update(
                    {id: $stateParams.account_id, update_token: $stateParams.token},
                    function(){
                        _this.success = true;
                    },
                    function(response){
                        if(response.data.error){
                            _this.error_message = response.data.error;
                        } else {
                            _this.error_message = 'Unexpected error ' + response.status;
                        }
                        _this.success = false;
                    }
                );
            };

            return ['$stateParams', 'ModelService', ApplyAccountChangesController];
        }
    );
}(define));