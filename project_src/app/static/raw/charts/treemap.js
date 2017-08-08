(function(){

	var tree = raw.models.tree();

	var chart = raw.chart()
        .title('矩形式树状图')
		.description(
            "矩形式树状结构绘图法，又称为矩形式树状结构图绘制法、树状结构矩形图绘制法，或者甚至称为树状结构映射，指的是一种利用嵌套式矩形来显示树状结构数据的方法。")
		.thumbnail("/static/raw/imgs/treemap.png")
	    .category('复杂层级')
		.model(tree)

	var width = chart.number()
		.title('宽度')
		.defaultValue(100)
		.fitToWidth(true)

	var height = chart.number()
		.title("高度")
		.defaultValue(500)

	var padding = chart.number()
		.title("Padding")
		.defaultValue(5)

	var colors = chart.color()
		.title("配色")

	chart.draw(function (selection, data){

		var format = d3.format(",d");

		var layout = d3.layout.treemap()
			.sticky(true)
            .padding(+padding())
            .size([+width(), +height()])
            .value(function(d) { return d.size; })

		var g = selection
    	    .attr("width", +width())
    	    .attr("height", +height())
    	  	.append("g")
    	    .attr("transform", "translate(.5,.5)");

		var nodes = layout.nodes(data)
	  	    .filter(function(d) { return !d.children; });

        colors.domain(nodes, function (d){ return d.color; });

		var cell = g.selectAll("g")
    	    .data(nodes)
    	    .enter().append("g")
    	    .attr("class", "cell")
    	    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

		cell.append("svg:rect")
    	    .attr("width", function (d) { return d.dx; })
    	    .attr("height", function (d) { return d.dy; })
    	    .style("fill", function (d) { return colors()(d.color); })
    	    .style("fill-opacity", function (d) {  return d.children ? 0 : 1; })
			.style("stroke","#fff")

		cell.append("svg:title")
			.text(function(d) { return d.name + ": " + format(d.size); });

		cell.append("svg:text")
    	    .attr("x", function(d) { return d.dx / 2; })
    	    .attr("y", function(d) { return d.dy / 2; })
    	    .attr("dy", ".35em")
    	    .attr("text-anchor", "middle")
	  //  .attr("fill", function (d) { return raw.foreground(color()(d.color)); })
    	   	.style("font-size","11px")
    		.style("font-family","Arial, Helvetica")
    	    .text(function(d) { return d.label ? d.label.join(", ") : d.name; });

	})
})();
