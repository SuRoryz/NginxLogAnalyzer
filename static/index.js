class socket {
	constructor (endpoint) {
		this.connection = io()//"", {transports: ["websocket"]})
	}
	
	send(event, data) {
		this.connection.emit(event, JSON.stringify(data))
	}
}

function convertFormToJSON(form) {
	const array = $(form).serializeArray(); // Encodes the set of form elements as an array of names and values.
	const json = {};
	$.each(array, function () {
	  json[this.name] = this.value || "";
	});
	return json;
  }

var CONFIG = new Object()

CONFIG.SERVER = "ALL"
CONFIG.TIMEGAP_PER = 60
CONFIG.TIMEGAP_WARN = 60
CONFIG.GRAPHIC_INTERVAL_PER = "h"
CONFIG.GRAPHIC_INTERVAL_WARN = "h"
CONFIG.TOP_IPS_BYWARN = false
CONFIG.MAX_LOGS_TERMINAL = 10
CONFIG.GROUP = "request_url"

function updateAll() {
	$socket.send("API:HOOK_LOGS", {server: CONFIG.SERVER})
	$socket.send("API:GET_LOGS", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_PER, count: CONFIG.MAX_LOGS_TERMINAL})
	$socket.send("API:GET_WARNS", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_WARN})

	$socket.send("API:GET_TOTALS", {server: CONFIG.SERVER})

	$socket.send("API:GET_TOP_IPS", {server: CONFIG.SERVER, by_warns: CONFIG.TOP_IPS_BYWARN, minutes_since: CONFIG.TIMEGAP_PER})
	$socket.send("API:GET_TOP_GROUP", {server: CONFIG.SERVER, param: CONFIG.GROUP, minutes_since: CONFIG.TIMEGAP_PER})

	$socket.send("API:GET_PER", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_PER})
	$socket.send("API:GET_WARNS_COUNT", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_WARN})
}

$(document).ready(function () {
	$socket = new socket("")
    updateAll()

	setInterval(() => {
		$socket.send("API:GET_PER", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_PER})
		$socket.send("API:GET_WARNS_COUNT", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_WARN})
	}, 5000)

	setInterval(() => {
		$socket.send("API:GET_TOP_IPS", {server: CONFIG.SERVER, by_warns: CONFIG.TOP_IPS_BYWARN, minutes_since: CONFIG.TIMEGAP_PER})
		$socket.send("API:GET_TOP_GROUP", {server: CONFIG.SERVER, param: CONFIG.GROUP, minutes_since: CONFIG.TIMEGAP_PER})
	}, 10000)

	setInterval(() => {
		$socket.send("API:GET_TOTALS", {server: CONFIG.SERVER})
	}, 3000)

	PER_CHART = new Chart(
		document.getElementById('plot-per-min-canvas'),
		{
		  type: 'line',
		  options: {
			responsive: true,
			maintainAspectRatio: false,
			hoverRadius: 30,
			pointRadius: 0,
			pointHoverRadius: 2,
			elements: {
				line: {
					borderWidth: 2
				}
			},
			fill: true,
			scales: {
				x: {
					ticks: {
						maxTicksLimit: 15,
						maxRotation: 90,
						minRotation: 90
					}
				}
			  },
			animation: true,
			plugins: {
			  legend: {
				display: false
			  },
			  hover: {
				mode: "point",
				intersect: false
			  },
			  tooltip: {
				enabled: true,
				intersect: false
			  }
			}
		  },
		  data: {
			tension: 0.1,
			labels: [],
			datasets: [{

			}
			]
		  }
		}
	  );
	
	  WARNS_CHART = new Chart(
		document.getElementById('plot-warns-graphic-canvas'),
		{
		  type: 'line',
		  options: {
			responsive: true,
			maintainAspectRatio: false,
			hoverRadius: 30,
			pointRadius: 0,
			pointHoverRadius: 2,
			elements: {
				line: {
					borderWidth: 2
				}
			},
			fill: true,
			scales: {
				x: {
					ticks: {
						maxTicksLimit: 15,
						maxRotation: 70,
						minRotation: 70
					}
				}
			  },
			animation: true,
			plugins: {
			  legend: {
				display: false
			  },
			  hover: {
				mode: "point",
				intersect: false
			  },
			  tooltip: {
				enabled: true,
				intersect: false
			  }
			}
		  },
		  data: {
			tension: 0.1,
			labels: [],
			datasets: [{

			}
			]
		  }
		}
	  );

	  TOP_IPS_CHART = new Chart(
		document.getElementById('plot-ips-canvas'),
		{
		  type: 'pie',
		options: {
			responsive: true,
			plugins: {
			legend: {
				position: 'top',
			},
			title: {
				display: true,
				text: 'Chart.js Pie Chart'
			}
			}
		},
		  data: {
			tension: 0.1,
			labels: [],
			datasets: [{

			}
			]
		  }
		}
	  );

	$socket.connection.on('API:GET_PER', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}

		d = {
			tension: 0.1,
			labels: msg.items.map(item => {
				let d = moment(Date.parse(item["key_as_string"])).utcOffset('+0100');
				switch (CONFIG.GRAPHIC_INTERVAL_PER) {
					case "h":
						lb = d.format("HH:mm:ss")
						break;
					case "d":
						lb = d.format("HH:mm:ss")
						break;
					case "m":
						lb = d.format("DD/HH/mm")
						break;
					case "all":
						lb = d.format("YYYY/MM/DD")
						break;
				}

				return lb
			}),
			datasets: [
			  {
				label: 'Hits',
				data:  msg.items.map(item => item["doc_count"]),
				borderColor: "#4865df",
			  }
			]
		}

		console.log(d.datasets)
		
		PER_CHART.data = d
		PER_CHART.update('none')
	});

	$socket.connection.on('API:GET_WARNS_COUNT', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}

		d = {
			tension: 0.1,
			labels: msg.items.map(item => {
				let d = moment(Date.parse(item["key_as_string"])).utcOffset('+0100')
				switch (CONFIG.GRAPHIC_INTERVAL_WARN) {
					case "h":
						lb = d.format("HH:mm:ss")
						break;
					case "d":
						lb = d.format("HH:mm:ss")
						break;
					case "m":
						lb = d.format("DD/HH/mm")
						break;
					case "all":
						lb = d.format("YYYY/MM/DD")
						break;
				}

				return lb
			}),
			datasets: [
			  {
				label: 'Warns',
				data:  msg.items.map(item => item["doc_count"]),
				borderColor: "#4865df",
			  }
			]
		}

		console.log(d.datasets)
		
		WARNS_CHART.data = d
		WARNS_CHART.update('none')
	});

	$socket.connection.on('API:GET_WARNS', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}

		if (!msg.append){
			$("#plot-warns-scroll").html("")
		}

		msg.items.forEach((item, index) => {
			item = item["_source"]
			if (CONFIG.SERVER != "ALL") {srv = " - " + CONFIG.SERVER} else {srv = ""}
			if (item["warn"]) {warn = " warn"} else {warn = ""}

			d = $("#plot-warns-scroll").append(`<div class="terminal-message-instance">
										<span class="log-time">[${item["time"].split("T")[1]}${srv}]</span>
										<span class="log-part log-addr ${warn}">${item["remote_addr"]}</span>
										<span data-n="request_url" class="log-part log-url">${item["request_url"]}</span>
										<span data-n="request_method" class="log-part log-method">${item["request_method"]}</span>
										<span data-n="request_protocol" class="log-part log-protocol">${item["resuest_protocol"]}</span> 
										<span data-n="request_status" class="log-part log-status">${item["request_status"]}</span>
										</div>`)
		});
	});

    $socket.connection.on('API:NEW_LOG', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}
        
		if (msg.new) {
			$("#terminal-body").html("");
		}

        msg.items.forEach((item, index) => {
			if (CONFIG.SERVER != "ALL") {srv = " - " + CONFIG.SERVER} else {srv = ""}
			if (item["warn"]) {warn = " warn"} else {warn = ""}

			d = $("#terminal-body").append(`<div class="terminal-message-instance">
										<span class="log-time">[${item["time"].split("T")[1]}${srv}]</span>
										<span class="log-addr ${warn}">${item["remote_addr"]}</span>
										<span data-n="request_url" class="log-part log-url">${item["request_url"]}</span>
										<span data-n="request_method" class="log-part log-method">${item["request_method"]}</span>
										<span data-n="resuest_protocol" class="log-part log-protocol">${item["resuest_protocol"]}</span> 
										<span data-n="request_status" class="log-part log-status">${item["request_status"]}</span>
										</div>`)
		});
	});

	$socket.connection.on('API:GET_TOP_IPS', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}

		d = {
			tension: 0.1,
			labels: msg.items.map(item => item["key"]),
			datasets: [
			  {
				label: 'Hits',
				data:  msg.items.map(item => item["doc_count"]),
				borderWidth: 0,
				backgroundColor: ["#34b7bb", "#BB9B34", "#BB3455"]
			  }
			]
		}
		TOP_IPS_CHART.data = d
		TOP_IPS_CHART.update('none')
        
		$("#plot-ips-val").html("")
        msg.items.forEach((item, index) => {
			warns_buckets = item["warns"]["buckets"]
			
			if (msg.by_warns) {
				d = $("#plot-ips-val").append(`<div class="terminal-message-instance"> <div class="ips-top-row-wrapper">
										<div class="ips-row-key">
											${item["key"]}
										</div>
										<div class="ips-row-count">
										</div>
										<div class="ips-row-warns">
											${item["doc_count"]}
										</div>
									</div></div>`)
				
				return
			}

			warns = 0
			if (warns) {
				warns.forEach((item_, index) => {
					if (item_["key"] == 1) warns = item["doc_count"]
				});
			}
			
			d = $("#plot-ips-val").append(`<div class="terminal-message-instance"><div class="ips-top-row-wrapper">
											<div class="ips-row-key">
												${item["key"]}
											</div>
											<div class="ips-row-count">
												${item["doc_count"]}
											</div>
											<div class="ips-row-warns">
												${warns}
											</div>
										</div></div>`)
		});
	});

	$socket.connection.on('API:GET_TOP_URLS', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}
        
		$("#plot-urls-val").html("")
        msg.items.forEach((item, index) => {
			d = $("#plot-urls-val").append(`<div class="terminal-message-instance">
												<div class="url-top-row-wrapper">
													<div class="url-row-key">
														${item["key"]}
													</div>
													<div class="url-row-count">
														${item["doc_count"]}
													</div>
													<div class="url-row-user">
														${item["top_user"]["buckets"][0]["key"]}
													</div>
													<div class="url-row-user-count">
														${item["top_user"]["buckets"][0]["doc_count"]}
													</div>
												</div>
											</div>`)
		});
	});

	$socket.connection.on('API:GET_TOP_GROUP', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}
        
		$(".url-row-key.head").text(CONFIG.GROUP)
		$("#plot-urls-val").html("")
        msg.items.forEach((item, index) => {
			d = $("#plot-urls-val").append(`<div class="terminal-message-instance">
												<div class="url-top-row-wrapper">
													<div class="url-row-key">
														${item["key"]}
													</div>
													<div class="url-row-count">
														${item["doc_count"]}
													</div>
													<div class="url-row-user">
														${item["top_user"]["buckets"][0]["key"]}
													</div>
													<div class="url-row-user-count">
														${item["top_user"]["buckets"][0]["doc_count"]}
													</div>
												</div>
											</div>`)
		});
	});

	$socket.connection.on('API:GET_TOTALS', function(msg) {
		if (!msg.status) {alert(msg.items[0]); return}
		
		$("#plot-hits-val").html(`<div class="plot-mini-text">${msg.items.hits.total} / ${msg.items.hits.today}</div>`)
        $("#plot-warns-val").html(`<div class="plot-mini-text">${msg.items.warns.total} / ${msg.items.warns.today}</div>`)
		$("#plot-flow-val").html(`<div class="plot-mini-text">${msg.items.flow.total} / ${msg.items.flow.today}</div>`)

	});

	$(".terminal-navbar-server").on("click", function(e) {
		CONFIG.SERVER = $(e.target).text();
		updateAll();

		$(".terminal-navbar-server.selected").removeClass("selected");
		$(e.target).addClass("selected");
	});

	$("#terminal-navbar-config-input").on("change", function(e) {
		CONFIG.MAX_LOGS_TERMINAL = parseInt($(e.target).val())
		$socket.send("API:GET_LOGS", {server: CONFIG.SERVER, count: CONFIG.MAX_LOGS_TERMINAL, minutes_since: CONFIG.TIMEGAP_PER})
	});

	$(".dashboard-item.hits").on("click", function(e) {
		CONFIG.TIMEGAP_PER = parseInt($(e.target).data("d"))
		CONFIG.GRAPHIC_INTERVAL_PER = $(e.target).data("n")

		$(".dashboard-item.hits.selected").removeClass("selected");
		$(e.target).addClass("selected");

		$socket.send("API:GET_PER", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_PER})
		$socket.send("API:GET_TOP_IPS", {server: CONFIG.SERVER, by_warns: CONFIG.TOP_IPS_BYWARN, minutes_since: CONFIG.TIMEGAP_PER})
		$socket.send("API:GET_TOP_URLS", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_PER})
	});

	$(".dashboard-item.warns").on("click", function(e) {
		CONFIG.TIMEGAP_WARN = parseInt($(e.target).data("d"))
		CONFIG.GRAPHIC_INTERVAL_WARN = $(e.target).data("n")

		$("#plot-warns-scroll").html("")

		$(".dashboard-item.warns.selected").removeClass("selected");
		$(e.target).addClass("selected");

		$socket.send("API:GET_WARNS", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_WARN})
		$socket.send("API:GET_WARNS_COUNT", {server: CONFIG.SERVER, minutes_since: CONFIG.TIMEGAP_WARN})
	});

	$('.switch-item').on("click", function(e) {
		$(".switch-item.selected").removeClass("selected");
		$(e.target).addClass("selected");

		CONFIG.TOP_IPS_BYWARN = $(e.target).data("n")
		$socket.send("API:GET_TOP_IPS", {server: CONFIG.SERVER, by_warns: CONFIG.TOP_IPS_BYWARN, minutes_since: CONFIG.TIMEGAP_PER})
	});

	$("body").on('click', ".log-part", function (e) {
		console.log($(e.target).data("n"))
		CONFIG.GROUP = $(e.target).data("n")

		$socket.send("API:GET_TOP_GROUP", {server: CONFIG.SERVER, param: CONFIG.GROUP, minutes_since: CONFIG.TIMEGAP_PER})
	});
});