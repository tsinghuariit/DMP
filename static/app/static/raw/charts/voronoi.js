(function(){

	var points = raw.models.points();

	points.dimensions().remove('size');
	points.dimensions().remove('label');

	var chart = raw.chart()
		.title('沃罗诺伊图')
		.description(
            "沃罗诺伊图（Voronoi Diagram，也称作 Dirichlet tessellation，狄利克雷镶嵌）是由俄国数学家格奥尔吉 · 沃罗诺伊建立的空间分割算法。灵感来源于笛卡尔用凸域分割空间的思想。在几何、晶体学建筑学、地理学、气象学、信息系统等许多领域有广泛的应用。")
		.thumbnail("/static/raw/imgs/voronoi.png")
		.category('弥散图')
		.model(points)

	var width = chart.number()
		.title("宽度")
		.defaultValue(1000)
		.fitToWidth(true)

	var height = chart.number()
		.title("高度")
		.defaultValue(500)

	var colors = chart.color()
		.title("配色")

	var showPoints = chart.checkbox()
		.title("Show points")
		.defaultValue(true)

	chart.draw(function (selection, data){

		var x = d3.scale.linear().range([0,+width()]).domain(d3.extent(data, function (d){ return d.x; })),
			y = d3.scale.linear().range([+height(), 0]).domain(d3.extent(data, function (d){ return d.y; }));

		var voronoi = d3.geom.voronoi()
			.x(function (d){ return x(d.x); })
			.y(function (d){ return y(d.y); })
    		.clipExtent([ [ 0, 0 ], [+width(), +height()] ]);

		var g = selection
		    .attr("width", +width())
		    .attr("height", +height())
		    .append("g");

		colors.domain(data, function (d){ return d.color; });

		var path = g.selectAll("path")
			.data(voronoi(data), polygon)
			.enter().append("path")
	      	.style("fill",function (d){ return d && colors()? colors()(d.point.color) :  "#dddddd"; })
	      	.style("stroke","#fff")
	      	.attr("d", polygon);

	  	path.order();

	  	g.selectAll("circle")
		    .data(data.filter(function(){ return showPoints() }))
		  	.enter().append("circle")
			  	.style("fill","#000000")
			  	.style("pointer-events","none")
			    .attr("transform", function (d) { return "translate(" + x(d.x) + ", " + y(d.y) + ")"; })
			    .attr("r", 1.5);

		function polygon(d) {
			if(!d) return;
		  return "M" + d.join("L") + "Z";
		}

	})
})();
