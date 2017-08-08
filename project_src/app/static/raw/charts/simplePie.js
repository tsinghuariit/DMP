(function(){

	var tree = raw.models.tree();

	var chart = raw.chart()
        .title('simplePie')
		.description(
            "简单的饼状图")
		.thumbnail("/static/raw/imgs/simplePie.png")
	    .category('饼图')
		.model(tree)

	var diameter = chart.number()
		.title('直径')
		.defaultValue(600)
		.fitToWidth(true)

	var colors = chart.color()
		.title("配色")

	chart.draw(function (selection, data){

		var radius = +diameter() / 2;

		var layout = d3.layout.partition()
		    .sort(null)
		    .size([2 * Math.PI, radius * radius])
		    .value(function(d) { return d.size; });

		var arc = d3.svg.arc()
		    .startAngle(function(d) { return d.x; })
		    .endAngle(function(d) { return d.x + d.dx; })
		    //.innerRadius(function(d) { return Math.sqrt(d.y); })
		    .outerRadius(function(d) { return Math.sqrt(d.y + d.dy); });

		var format = d3.format(",d");

		var g = selection
    	    .attr("width", +diameter())
    	    .attr("height", +diameter())
    	  	.append("g")
    	    .attr("transform", "translate(" + (+diameter() / 2) + "," + (+diameter() / 2) + ")");

		var nodes = layout.nodes(data);

		colors.domain(nodes, function (d){ return seek(d); });

		var slicesGroups = g.selectAll("g")
    	    .data(nodes)
		    .enter().append("g")
		    //.attr("display", function(d) { return d.depth ? null : "none"; }) // hide inner ring

		slicesGroups.append("path")
			.attr("d", arc)
		      //.style("stroke", "#fff")
		      .style("fill", function(d) { return colors()(seek(d)); })
		      .style("fill-rule", "evenodd")

		slicesGroups.append("text")
		      .attr("transform", function(d) { return "rotate(" + (d.x + d.dx / 2 - Math.PI / 2) / Math.PI * 180 + ")"; })
		      .attr("x", function(d) { return Math.sqrt(d.y); })
		      .attr("dx", "6")
		      .attr("dy", ".35em")
		      .style("font-size","11px")
              .style("font-family","Arial, He	lvetica")
		      .text(function(d) { return d.label ? d.label.join(", ") : d.name; });

		slicesGroups.append("title")
		 	.text(function(d) {
		 		var size = d.size ? format(d.size) : "none";
		 		return d.name + ": " + size;
		 	});

		 function seek(d){
		 	if (d.children) return seek(d.children[0]);
		 	else return d.color;
		 }

	})
})();
