'use strict';

angular.module('raw', [
  'ngRoute',
  'ngAnimate',
  'ngSanitize',
  'raw.filters',
  'raw.services',
  'raw.directives',
  'raw.controllers',
  'mgcrea.ngStrap',
  'ui',
  'colorpicker.module',
  'ngFileUpload'
  // 'raw.tabs'
])

.config(['$routeProvider','$locationProvider', function ($routeProvider,$locationProvider) {
  $routeProvider.when('/raw', {templateUrl: '/static/raw/partials/main.html', controller: 'RawCtrl'})
  //.when('/detail', {templateUrl: 'partials/main.html', controller: 'RawCtrl'})
  //.when('/simple/*path', {templateUrl: 'partials/simple.html', controller: 'simple_controller'})
  .otherwise({redirectTo: '/'});
  $locationProvider.html5Mode(true);
}]);
