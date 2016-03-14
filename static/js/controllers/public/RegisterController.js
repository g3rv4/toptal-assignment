(function (define) {
    define(
        ['angular'],
        function () {
            var RegisterController = function (ModelService) {
                var _this = this;
                _this.form = {};

                _this.submit = function(){
                    _this.form.sent = true;

                    if(_this.formElement.$valid && _this.form.password == _this.form.password2) {
                        var Registration = ModelService['Registration'];
                        var reg = new Registration({
                            email: _this.form.email,
                            password: _this.form.password
                        });
                        reg.$save();
                    }
                }
            };

            return ['ModelService', RegisterController];
        }
    );
}(define));