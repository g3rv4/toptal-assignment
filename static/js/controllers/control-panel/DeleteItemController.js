(function (define) {
    define(
        [],
        function () {
            var DeleteItemController = function ($uibModalInstance, item) {
                var _this = this;
                _this.item = item;

                _this.ok = function(){
                    $uibModalInstance.close();
                };

                _this.cancel = function(){
                    $uibModalInstance.dismiss('cancel');
                };
            };

            return ['$uibModalInstance', 'item', DeleteItemController];
        }
    );
}(define));
