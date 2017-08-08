'use strict';

angular.module('raw.tabs', [])
  .controller('TabController', ['$scope', function($scope) {
    $scope.tab = 'data';

    $scope.rawTabs = function(newTab){
      $scope.tab = newTab;
    };

    $scope.isSet = function(tabName){
      return $scope.tab === tabName;
    };
}]);
