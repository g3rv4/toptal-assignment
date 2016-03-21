requirejs.config({
    "baseUrl": "/static/js/",
    "paths": {
        "lodash": "../components/lodash/lodash",

        "jquery": "../components/jquery/dist/jquery",
        "angular": "../components/angular/angular",

        "ng-local-storage": "../components/angular-local-storage/dist/angular-local-storage",
        "ng-ui-router": "../components/angular-ui-router/release/angular-ui-router",
        "ng-resource": "../components/angular-resource/angular-resource",
        "ng-bootstrap": "../components/angular-bootstrap/ui-bootstrap-tpls",
        "ng-animate": '../components/angular-animate/angular-animate',
        "moment": "../components/moment/moment"
    },
    "shim": {
        "angular": {
            "deps": ["jquery"],
            "exports": "angular"
        },
        "ng-local-storage": ['angular'],
        "ng-ui-router": ['angular'],
        "ng-resource": ['angular'],
        "ng-bootstrap": ['angular'],
        "ng-animate": ['angular'],
        "moment": {
            exports: 'moment'
        }
    }
});
