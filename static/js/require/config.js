requirejs.config({
    "baseUrl": "/static/js/",
    "paths": {
        "lodash": "../components/lodash/lodash",

        "jquery": "../components/jquery/dist/jquery",
        "angular": "../components/angular/angular",

        "ng-local-storage": "../components/angular-local-storage/dist/angular-local-storage",
        "ng-ui-router": "../components/angular-ui-router/release/angular-ui-router",

        "metis-menu": "../components/metisMenu/src/metisMenu",
        "sb-admin": "../components/startbootstrap-sb-admin-2/dist/js/sb-admin-2"
    },
    "shim": {
        "angular": {
            "deps": ["jquery"],
            "exports": "angular"
        },
        "metis-menu": ['jquery'],
        "sb-admin": ['metis-menu', 'jquery'],
        "ng-local-storage": ['angular'],
        "ng-ui-router": ['angular']
    }
});
