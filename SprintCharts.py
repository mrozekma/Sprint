from __future__ import division
from collections import OrderedDict
from itertools import cycle
from math import ceil
from string import uppercase as alphabet

from Chart import Chart
from Task import Task, statuses, statusMenu
from Availability import Availability
from utils import *

colors = ['#4572a7', '#aa4643', '#89a54e', '#80699b', '#3d96ae', '#db843d', '#92a8cd', '#a47d7c', '#b5ca92']
colorMap = { # Maps status names to chart colors
	'blocked': '#4572a7',
	'canceled': '#000',
	'complete': '#89a54e',
	'deferred': '#80699b',
	'in progress': '#b47c19',
	'not started': '#aa4643',
	'split': '#db843d'
}

def setupTimeline(chart, sprint, skippedSeries = []):
	chart.tooltip.formatter = """
function() {
	if(this.point != undefined) { // flag
		return this.point.text;
	}
	rtn = '<span style="font-size: 7pt">' + this.points[0].point.name + '</span><br>';
	this.points.forEach(function(point) {
		if(%s) {return;}
		rtn += '<span style="color: ' + point.series.color + '">' + point.series.name + '</span>: <b>' + point.y + '</b><br>';
	});
	return rtn;
}
""" % ('false' if skippedSeries == [] else ' || '.join("point.series.name == '%s'" % series for series in skippedSeries))
	chart.xAxis.categories = [day.strftime('%a') for day in sprint.getDays()]
	for series in chart.series.get():
		if series.get('type', '') not in ('flags', 'waterfall'):
			series['data'] = [[a, b] for (a, b) in zip([day.strftime('%A, %b %d, %Y') for day in sprint.getDays()], series['data'])]

class HoursChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)
		futureIndex = days.index(futureStarts) if futureStarts else None

		tasks = sprint.getTasks(includeDeleted = True)

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.title.text = ''
		self.plotOptions.line.dataLabels.enabled = True
		self.tooltip.shared = True
		self.credits.enabled = False
		with self.xAxis as xAxis:
			xAxis.tickmarkPlacement = 'on'
			xAxis.maxZoom = 1
			xAxis.title.text = 'Day'
			# Future bar
			if futureIndex is not None:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': futureIndex - 0.75,
					'to': len(days) - 0.5
				}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Hours'
		self.series = seriesList = []

		taskSeries = {
			'id': 'taskSeries',
			'name': 'Tasking',
			'data': [],
			'color': '#4572a7',
			'zIndex': 2
		}
		seriesList.append(taskSeries)

		availSeries = {
			'name': 'Availability',
			'data': [],
			'color': '#aa4643',
			'zIndex': 2
		}
		seriesList.append(availSeries)

		flagSeries = {
			'type': 'flags',
			'data': [],
			'color': '#4572a7',
			'shape': 'flag',
			'onSeries': 'taskSeries',
			'showInLegend': False,
			'y': 16
		}
		seriesList.append(flagSeries)

		if futureIndex == 0:
			futureIndex = 1

		statusToday, hoursToday = None, None
		for day in days[:futureIndex]:
			tasksToday = [t.getRevisionAt(day) for t in tasks]
			statusYesterday, hoursYesterday = statusToday, hoursToday
			statusToday = {t: t.status for t in tasksToday if t and not t.deleted}
			hoursToday = {t: t.manHours() for t in tasksToday if t and not t.deleted}
			taskSeries['data'].append(sum(hoursToday.values()))

			if hoursYesterday:
				hoursDiff = {t: hoursToday.get(t, 0) - hoursYesterday.get(t, 0) for t in hoursToday}
				largeChanges = [t for t, h in hoursDiff.iteritems() if abs(h) >= 16]
				if largeChanges:
					texts = []
					for t in largeChanges:
						if t not in hoursYesterday:
							texts.append("<span style=\"color: #f00\">(New +%d)</span> %s" % (t.hours, t.name))
						elif hoursDiff[t] > 0:
							texts.append("<span style=\"color: #f00\">(+%d)</span> %s" % (hoursDiff[t], t.name))
						else:
							if t.status in ('in progress', 'not started'):
								texts.append("<span style=\"color: #0a0\">(%d)</span> %s" % (hoursDiff[t], t.name))
							elif t.status == 'complete':
								texts.append("<span style=\"color: #0a0\">(Complete %d)</span> %s" % (hoursDiff[t], t.name))
							else:
								texts.append("<span style=\"color: #999\">(%s %d)</span> %s" % (statuses[t.status].getRevisionVerb(statusYesterday.get(t, 'not started')), hoursDiff[t], t.name))
					flagSeries['data'].append({'x': days.index(day), 'title': alphabet[len(flagSeries['data']) % len(alphabet)], 'text': '<br>'.join(texts)})

		avail = Availability(sprint)
		for day in days:
			availSeries['data'].append(avail.getAllForward(day))

		setupTimeline(self, sprint, ['Projected tasking'])

		# Add commitment percentage to the axis label
		labels = self.xAxis.categories.get()
		for i in range(len(labels)):
			# For future percentages, use today's hours (i.e. don't use the projected hours)
			needed = taskSeries['data'][min(i, futureIndex - 1) if futureIndex else i][1]
			thisAvail = availSeries['data'][i][1]
			pcnt = "%d" % (needed * 100 / thisAvail) if thisAvail > 0 else "inf"
			labels[i] += "<br>%s%%" % pcnt
		self.xAxis.categories = labels
		self.xAxis.labels.formatter = "function() {return this.value.replace('inf', '\u221e');}"

		# Trendline
		data = self.series[0].data.get()
		dailyAvail = dict((day, avail.getAll(day)) for day in days)
		totalAvail = 0
		for daysBack in range(1, (futureIndex or 0) + 1):
			midPoint = [futureIndex - daysBack, data[futureIndex - daysBack][1]]
			if dailyAvail[days[midPoint[0]]] > 0:
				daysBack = min(daysBack + 2, futureIndex)
				startPoint = [futureIndex - daysBack, data[futureIndex - daysBack][1]]
				totalAvail = sum(dailyAvail[day] for day in days[startPoint[0] : midPoint[0]])
				break

		if totalAvail > 0 and startPoint[0] != midPoint[0]:
			slope = (midPoint[1] - startPoint[1]) / (midPoint[0] - startPoint[0])
			slopePerAvail = slope * (midPoint[0] - startPoint[0]) / totalAvail
			points, total = [], midPoint[1]
			total = taskSeries['data'][futureIndex - 1][1]
			points.append([futureIndex - 1, total])
			for i in range(futureIndex, len(days)):
				total += slopePerAvail * dailyAvail[days[i]]
				points.append([i, total])
			seriesList.append({
				'name': 'Projected tasking',
				'data': points,
				'color': '#666',
				'dataLabels': {'formatter': "function() {return (this.point.x == %d) ? parseInt(this.y, 10) : null;}" % (len(days) - 1)},
				'marker': {'symbol': 'circle'},
				'zIndex': 1
			})

class StatusChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)
		futureIndex = days.index(futureStarts) if futureStarts else None

		tasks = sprint.getTasks()

		self.chart.type = 'area'
		self.title.text = ''
		self.plotOptions.area.stacking = 'percent'
		self.plotOptions.area.marker.enabled = False
		self.tooltip.shared = True
		self.credits.enabled = False
		with self.xAxis as xAxis:
			xAxis.tickmarkPlacement = 'on'
			xAxis.maxZoom = 1
			xAxis.title.text = 'Day'
			xAxis.categories = [day.strftime('%a') for day in sprint.getDays()]
			# Future bar
			if futureIndex:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': futureIndex - 0.75,
					'to': len(days) - 0.5,
					# 'zIndex': 5
				}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Percentage of tasks'
		self.series = seriesList = []

		counts = OrderedDict((name, []) for block in statusMenu for name in block)
		self.colors = [colorMap[type] for type in counts]
		for type, count in counts.iteritems():
			seriesList.append({
				'name': statuses[type].text,
				'data': count
			})

		for day in days:
			tasksToday = [t.getRevisionAt(day) for t in tasks]
			for type, count in counts.iteritems():
				count.append(len(filter(lambda task: task and task.status == type, tasksToday)))

		setupTimeline(self, sprint)

class EarnedValueChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)
		futureIndex = days.index(futureStarts) if futureStarts else None

		tasks = sprint.getTasks()

		self.chart.type = 'waterfall'
		self.tooltip.enabled = False
		self.title.text = ''
		self.legend.enabled = False
		self.credits.enabled = False
		with self.plotOptions.series.dataLabels as labels:
			labels.enabled = True
			labels.formatter = """
function() {
	sum = 0;
	max_x = this.point.x;
	for(i in this.series.points) {
		point = this.series.points[i];
		sum += point.y;
		if(point.x == max_x) {
			break;
		}
	}
	return sum;
}
"""
			# labels.color = '#fff'
			labels.verticalAlign = 'top'
			labels.y = -20

		with self.xAxis as xAxis:
			xAxis.type = 'category'
			xAxis.tickmarkPlacement = 'on'
			xAxis.categories = [day.strftime('%a') for day in sprint.getDays()]
			# Future bar
			if futureIndex:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': futureIndex - 0.75,
					'to': len(days) - 0.5
				}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Hours'
		self.series = seriesList = []

		series = {
			'type': 'waterfall',
			'name': 'Earned value',
			'data': [],
			'upColor': '#4572a7',
			'color': '#aa4643'
		}
		seriesList.append(series)

		yesterdaySum = 0
		for day in days:
			dayTasks = [t.getRevisionAt(day) for t in tasks]
			todaySum = sum(t.earnedValueHours() for t in dayTasks if t)
			series['data'].append(todaySum - yesterdaySum)
			yesterdaySum = todaySum

		setupTimeline(self, sprint)

class HoursByUserChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)
		futureIndex = days.index(futureStarts) if futureStarts else None

		tasks = sprint.getTasks(includeDeleted = True)

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.title.text = ''
		self.tooltip.shared = True
		self.credits.enabled = False
		with self.xAxis as xAxis:
			xAxis.tickmarkPlacement = 'on'
			xAxis.maxZoom = 1
			xAxis.title.text = 'Day'
			# Future bar
			if futureIndex:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': futureIndex - 0.75,
					'to': len(days) - 0.5
				}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Hours'
		self.series = seriesList = []

		for user in sorted(sprint.members):
			series = {
				'name': user.username,
				'data': []
			}
			seriesList.append(series)

			for day in days:
				series['data'].append(sum(t.hours if t and user in t.assigned and not t.deleted else 0 for t in [t.getRevisionAt(day) for t in tasks]))

		setupTimeline(self, sprint)

class CommitmentChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)

		tasks = sprint.getTasks()
		start = tsToDate(sprint.start)

		self.title.text = ''
		self.tooltip.formatter = "function() {return '<b>' + this.series.name + '</b><br>' + this.point.name + ': '+ this.point.x + ' (' + this.y + '%)';}"
		self.credits.enabled = False
		self.series = seriesList = []

		series = {
			'type': 'pie',
			'name': 'Start',
			'size': '45%',
			'innerSize': '20%',
			'showInLegend': True,
			'dataLabels': {'enabled': False},
			'data': []
		}
		seriesList.append(series)

		originalTasks = filter(None, (task.getStartRevision(False) for task in tasks))
		clrGen = cycle(colors)
		total = sum(t.hours for t in originalTasks)
		for user in sorted(sprint.members):
			hours = sum(t.hours for t in originalTasks if user in t.assigned)
			series['data'].append({
				'name': user.username,
				'x': hours,
				'y': float("%2.2f" % (100 * hours / total if total > 0 else 0)),
				'color': clrGen.next()
			})

		series = {
			'type': 'pie',
			'name': 'Now',
			'innerSize': '45%',
			'dataLabels': {'enabled': False},
			'data': []
		}
		seriesList.append(series)

		clrGen = cycle(colors)
		total = sum(t.hours for t in tasks)
		for user in sorted(sprint.members):
			hours = sum(t.hours for t in tasks if user in t.assigned)
			series['data'].append({
				'name': user.username,
				'x': hours,
				'y': float("%2.2f" % (100 * hours / total if total > 0 else 0)),
				'color': clrGen.next()
			})

class TaskChart(Chart):
	def __init__(self, placeholder, tasks):
		Chart.__init__(self, placeholder)

		many = isinstance(tasks, list)
		if not many:
			tasks = [tasks]
		if len(set(task.sprint for task in tasks)) > 1:
			raise Exception("All tasks must be in the same sprint")

		sprint = tasks[0].sprint if len(tasks) > 0 else None

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.title.text = ''
		self.tooltip.formatter = "function() {idx = this.series.name.indexOf(':'); return '<small>' + Highcharts.dateFormat('%A, %B %e, %Y', this.x) + '</small><br><span style=\"color: ' + this.series.color + '\">' + this.series.name.slice(idx + 1) + '</span>: ' + this.y + (this.y == 1 ? ' hour' : ' hours')}"
		self.plotOptions.line.dataLabels.enabled = not many
		self.plotOptions.line.dataLabels.x = -10
		self.plotOptions.line.step = True
		self.legend.enabled = False
		self.credits.enabled = False
		with self.xAxis as x:
			x.type = 'datetime'
			x.dateTimeLabelFormats.day = '%a'
			x.tickInterval = 24 * 3600 * 1000
			x.maxZoom = 24 * 3600 * 1000
			if sprint:
				x.min = (sprint.start - 24*3600) * 1000
				x.max = sprint.end * 1000
			x.title.text = 'Day'
		with self.yAxis as y:
			y.min = 0
			y.tickInterval = 4
			y.minorTickInterval = 1
			y.title.text = 'Hours'

		self.series = seriesList = []
		for task in tasks:
			revs = task.getRevisions()
			series = {
				'name': "%d:%s" % (task.id, task.name) if many else 'Hours',
				'data': [],
				}
			if many:
				series['events'] = {'click': "function() {window.location = '/tasks/%d';}" % task.id}
			seriesList.append(series)

			hoursByDay = dict((tsStripHours(rev.timestamp), rev.hours) for rev in revs)
			hoursByDay[tsStripHours(min(dateToTs(getNow()), task.historyEndsOn()))] = task.hours
			series['data'] += [(utcToLocal(date) * 1000, hours) for (date, hours) in sorted(hoursByDay.items())]

class GroupGoalsChart(Chart):
	def __init__(self, group):
		Chart.__init__(self, 'group-goals-chart')
		tasks = group.getTasks()
		goals = set(task.goal for task in tasks)

		self.title.text = ''
		self.plotOptions.pie.dataLabels.enabled = True
		self.tooltip.formatter = "function() {return this.point.name + ': '+ this.point.x + (this.point.x == 1 ? ' task' : ' tasks') + ' (' + this.y + '%)';}"
		self.credits.enabled = False
		self.series = [{
			'type': 'pie',
			'name': 'Sprint Goals',
			'data': [{
				'name': goal.name if goal else 'Other',
				'color': goal.getHTMLColor() if goal else '#ccc',
				'x': sum(task.goal == goal or False for task in tasks)
			} for goal in goals]
		}]

		# Percentages
		for m in self.series[0].data.get():
			m['y'] = float("%2.2f" % (m['x'] * 100 / len(tasks)))
