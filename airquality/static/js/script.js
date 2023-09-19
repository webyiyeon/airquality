String.prototype.format = function() {
  var args = arguments;
  return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined' ? args[number] : match;
  });
};

/* 지도 생성 */
var map = L.map('map').setView([36.34, 127.77], 7);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
}).addTo(map);

/* 변수 선언 */

/* 대기질 지수(CAI) 변수 및 함수 선언부 */
var htmlTemplate = "<table>"
    + " <tr> <th colspan='2' class='value {0}'> <b>{1}</b></th> </tr>"
    + " <tr> <td colspan='2' class='value'> <b> 주요 오염물질 </b></td> </tr>"
    + " <tr> <td colspan='2' class='value'> {2}</td> </tr>"
    + " <tr> <td colspan='2' class='value'> <b> 상세 대기 정보</b> </td> </tr>"
    + " <tr> <td> PM10 </td> <td class='value'>{3}</td> </tr>"
    + " <tr> <td> PM25 </td> <td class='value'>{4}</td> </tr>"
    + " <tr> <td> CO </td> <td class='value'>{5}</td> </tr>"
    + " <tr> <td> O3 </td> <td class='value'>{6}</td> </tr>"
    + " <tr> <td> SO2 </td> <td class='value'>{7}</td> </tr>"
    + " <tr> <td> NO2 </td> <td class='value'>{8}</td> </tr>"
    + "</table>";

var CAIGroup = L.markerClusterGroup({
  iconCreateFunction: function (cluster) {
    className = 'custom-cluster'
    // find station_dist
    var uniqueDist = [];

    // calculate average of CAI
    var sumCAI = 0;
    var count = cluster.getChildCount();

    // city info
    var city = "";

    cluster.getAllChildMarkers().forEach(function (marker) {
      sumCAI += marker.options.CAI;
      var dist = marker.options.dist;
      city = marker.options.city.trim();
      if (uniqueDist.indexOf(dist) === -1){
        uniqueDist.push(dist);
      }
    });
    var avgCAI = sumCAI / count;
    var dist = "";
    if (uniqueDist.length == city_dist[city].length) {
      dist = city
    } else {
      dist = uniqueDist[0]
    }

    // color matching 
    if (avgCAI >= 251) {className += ' cluster-red';} 
    else if (avgCAI >= 101) {className += ' cluster-yellow';} 
    else if (avgCAI >= 51) {className += ' cluster-green';} 
    else {className += ' cluster-blue';};

    return L.divIcon({
      className: className,
      html: "<div class='cluster_text'>" + dist + "<br> <span>" + avgCAI.toFixed(0) + "</span> </div>",
      iconSize: [40, 40]
    })
  }
});

function showCAI() { 
  if (map.hasLayer(CAIGroup)){
    map.removeLayer(CAIGroup);
    CAIGroup.clearLayers();
  }else {
    var addedLocations = {};
    for(let i=0; i<air_quality.length; i++){
        var item = air_quality[i];
        var locationId = item.station_cd;
        if (!addedLocations[locationId]){
          addedLocations[locationId] = true;
          className = 'custom-marker'
    
          if (item.CAI >= 251) {className += ' marker-red'; table_class = 'verybad';} 
          else if (item.CAI >= 101) {className += ' marker-yellow'; table_class = 'bad';} 
          else if (item.CAI >= 51) {className += ' marker-green'; table_class = 'average';} 
          else {className += ' marker-blue'; table_class = 'good';};
    
          var customIcon = L.divIcon({
              className: className,
              html: "<div class='marker_text'>" + item.station_nm + "<br> <span>" + item.CAI + "</span> </div>",
              iconSize: [60, 40],
          });
          var formattedHtml = htmlTemplate.format(
              table_class,
              item.station_nm,
              item.pltnt_cd,
              item.PM10,
              item.PM25,
              item.CO,
              item.O3,
              item.SO2,
              item.NO2
          );
          var marker = L.marker([item.latitude, item.longitude], {
            icon: customIcon,
            CAI: item.CAI,
            dist: item.station_dist,
            city: item.station_city,
          }, KeyboardEvent=true, riseOnHover=true).bindPopup(formattedHtml);
          
          CAIGroup.addLayer(marker);
        }
    }
    map.addLayer(CAIGroup)
  }
}

/* 대기 예보 API 변수 및 함수 선언부 */
var forecastGroup = new L.LayerGroup();



function showForecast(pltnt_cd, inform_date) {
  if (pltnt_cd === "Close") {
    map.removeLayer(forecastGroup);
    forecastGroup.clearLayers();
    return;
  }
  if (map.hasLayer(forecastGroup)) {
    // 이미 마커가 있으면 지우기
    map.removeLayer(forecastGroup);
    forecastGroup.clearLayers();
  }
  if (forecast[pltnt_cd]) {
    const keys = Object.keys(forecast[pltnt_cd]);
    if (keys.includes(inform_date)){
      var each_forecast = forecast[pltnt_cd][inform_date];
      for (var i = 0; i < each_forecast.length; i++) {
        var item = each_forecast[i];
        
        // item.grade에 따라 클래스 이름 설정
        var gradeClassName = "";
        if (item.grade === "좋음") {
          gradeClassName = "good";
        } else if (item.grade === "보통") {
          gradeClassName = "average";
        } else if (item.grade === "나쁨") {
          gradeClassName = "bad";
        } else if (item.grade === "매우 나쁨") {
          gradeClassName = "verybad";
        }
        
        var forecastIcon = L.divIcon({
          className: "forecast-marker " + gradeClassName, // 클래스 이름 추가
          iconSize: [60, 40],
          html: "<div class='marker_text'> " + item.city + "<br><span>" + item.grade + "</span></div>"
        });
        
        var forecast_marker = L.marker(
          [item.latitude, item.longitude], {
            icon: forecastIcon,
          })
          .bindPopup("<table> 도시:" + item.city + "</br> 통보 시간: " + item.datetime + "</table>");
          
        forecastGroup.addLayer(forecast_marker); // 마커를 그룹에 추가합니다.
      }
    }
    forecastGroup.addTo(map)
  }
}
