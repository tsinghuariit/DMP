(function(){

	// A simple scatterplot for APIs demo

	// The Model

	var model = raw.model();

	// X axis dimension
	// Adding a title to be displayed in the UI
 	// and limiting the type of data to Numbers only
	var x = model.dimension()
		.title('X 轴')
		.types(Number, Date, String)
        .accessor(function (d){ return this.type() == "Date" ? Date.parse(d) : this.type() == "String" ? d : +d; })
        .required(1)

	// Y axis dimension
	// Same as X
	var y = model.dimension()
		.title('Y 轴')
		.types(Number)

	// Mapping function
	// For each record in the data returns the values
	// for the X and Y dimensions and casts them as numbers
	model.map(function (data){
		return data.map(function (d){
			return {
				x : +x(d),
				y : +y(d),
			}
		})
	})


	// The Chart

	var chart = raw.chart()
		.title('线性图')
        .thumbnail("/static/raw/imgs/line.png")
        .description("简单的线性图")
        .category('线性图')
		.model(model)


	// Some options we want to expose to the users
	// For each of them a GUI component will be created
	// Options can be use within the Draw function
	// by simply calling them (i.e. witdh())
	// the current value of the options will be returned

	// Width
	var width = chart.number()
		.title('宽度')
		.defaultValue(600)

	// Height
	var height = chart.number()
		.title('高度')
		.defaultValue(500)

	// A simple margin
	var margin = chart.number()
		.title('间距')

		.defaultValue(10)
	var padding = chart.number()
		.title('垂直间距')
		.defaultValue(0);

	// Padding between bars
	var xPadding = chart.number()
		.title('水平间距')
		.defaultValue(0.1);

	// Use or not the same scale across all the bar charts
	var sameScale = chart.checkbox()
        .title("使用相同的缩放倍率")
        .defaultValue(false)

	// Chart colors
	var colors = chart.color()
        .title("配色")
	// Drawing function
	// selection represents the d3 selection (svg)
	// data is not the original set of records
	// but the result of the model map function
	chart.draw(function (selection, data){
		// svg size
		selection
			.attr("width", width())
			.attr("height", height())

		// x and y scale
		var margin = {top: 0, right: 0, bottom: 50, left: 50};

		var titleSpace = 30;
		//var xScale = d3.time.scale().rangeRound([0, width()]);
		var xScale = x.type() == "Date"
			? d3.time.scale().rangeRound([0, width()])
			: d3.scale.linear().rangeRound([0, width()])
		
		var yScale = d3.scale.linear().rangeRound([height(),0]);

		var w = +width() - margin.left,
			h = (+height() - margin.bottom - ((titleSpace + padding()) * (data.length - 1))) / data.length;

		var index = 1;
		linechart = selection.append("g")
      		.attr("transform", "translate(" + margin.left + "," + index * (h + padding() + titleSpace) + ")")

		
		xScale.domain( d3.extent(data, function (d){ return d.x; }) );
		yScale.domain(d3.extent(data, function (d){ return d.y; }));

		var line = d3.svg.line()
    		.x(function(d) { return xScale(d.x); })
    		.y(function(d) { return yScale(d.y); });

		linechart.append("g")
			// .attr("transform", "translate(" + margin.left + "," + ((h + padding() + titleSpace) * data.length - padding()) + ")")
     		.attr("transform", "translate(" + 0 + "," + (height()-20) + ")")
      		.call(d3.svg.axis().scale(xScale).orient("bottom"))
    		.select(".domain")
      		.remove();

		// linechart.append("g")
		// 	.attr("class", "y axis")
		// 	.style("font-size","10px")
		// 	.style("font-family","Arial, Helvetica")
		// 	.attr("transform", "translate(0," + titleSpace + ")")
		// 	.call(d3.svg.axis().scale(yScale).orient("left").ticks(h/15));

		linechart.append("g")
			.attr("transform", "translate(margin.left,20)")
			.call(d3.svg.axis().scale(yScale).orient("left"))				
			.append("text")
			.attr("fill", "#000")
			.attr("transform", "rotate(-90)")
			.attr("y", 3)
			.attr("dy", "0.41em")
			.attr("text-anchor", "end");

		linechart.append("path")
			.datum(data)
			.attr("fill", "none")
			.attr("stroke", "steelblue")
			.attr("stroke-linejoin", "round")
			.attr("stroke-linecap", "round")
			.attr("stroke-width", 1.5)
			.attr("d", line);

		// selection.append("g")
		// 	.selectAll("path")
		// 	.data(data)
		// 	.enter().append("path")
		// 	.attr("fill", "none")
		// 	.attr("stroke", "steelblue")
		// 	.attr("stroke-linejoin", "round")
		// 	.attr("stroke-linecap", "round")
		// 	.attr("stroke-width", 1.5)
		// 	.attr("d", line);

	})
})();


