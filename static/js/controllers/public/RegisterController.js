(function (define) {
    define(
        [],
        function () {
            var RegisterController = function (ModelService) {
                var _this = this;
                _this.form = {};

                _this.submit = function(){
                    _this.form.sent = true;

                    if(_this.formElement.$valid && _this.form.password == _this.form.password2) {
                        var Account = ModelService['Account'];
                        var reg = new Account({
                            name: _this.form.name,
                            email: _this.form.email,
                            password: _this.form.password
                        });
                        reg.$save(function(){
                            _this.success = true;
                        }, function(response){
                            if(response.data.error){
                                _this.error_message = response.data.error;
                            } else {
                                _this.error_message = 'Unexpected error ' + response.status;
                            }
                            _this.success = false;
                        });
                    }
                }
            };

            return ['ModelService', RegisterController];
        }
    );
}(define));