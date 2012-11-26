from __future__ import division
from itertools import cycle
from math import ceil

from Chart import Chart
from Task import Task
from Availability import Availability
from utils import *

def setupTimeline(chart, sprint, skippedSeries = []):
	chart.tooltip.formatter = """
function() {
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
			'name': 'Tasking',
			'data': [],
			'zIndex': 2
		}
		seriesList.append(series)

		for day in days[:futureIndex]:
			series['data'].append(sum(t.manHours() if t and not t.deleted else 0 for t in [t.getRevisionAt(day) for t in tasks]))

		series = {
			'name': 'Availability',
			'data': [],
			'zIndex': 2
		}
		seriesList.append(series)

		avail = Availability(sprint)
		for day in days:
			series['data'].append(avail.getAllForward(day))

		setupTimeline(self, sprint, ['Projected tasking'])

		# Add commitment percentage to the axis label
		labels = self.xAxis.categories.get()
		for i in range(len(labels)):
			# For future percentages, use today's hours (i.e. don't use the projected hours)
			needed = seriesList[0]['data'][min(i, futureIndex - 1) if futureIndex else i][1]
			thisAvail = seriesList[1]['data'][i][1]
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
			total = seriesList[0]['data'][futureIndex - 1][1]
			points.append([futureIndex - 1, total])
			for i in range(futureIndex, len(days)):
				total += slopePerAvail * dailyAvail[days[i]]
				points.append([i, total])
			self.series.get().append({
				'name': 'Projected tasking',
				'data': points,
				'color': '#666',
				'dataLabels': {'formatter': "function() {return (this.point.x == %d) ? parseInt(this.y, 10) : null;}" % (len(days) - 1)},
				'marker': {'symbol': 'circle'},
				'zIndex': 1
			})

class EarnedValueChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)
		futureIndex = days.index(futureStarts) if futureStarts else None

		tasks = sprint.getTasks()

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.colors = ['#89A54E', '#80699B']
		self.title.text = ''
		self.plotOptions.line.dataLabels.enabled = True
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

		series = {
			'name': 'Earned value',
			'data': []
		}
		seriesList.append(series)

		for day in days:
			dayTasks = [t.getRevisionAt(day) for t in tasks]
			series['data'].append(sum(t.earnedValueHours() for t in dayTasks if t))

		series = {
			'name': 'Deferred tasks',
			'data': []
		}
		seriesList.append(series)

		for day in days:
			series['data'].append(sum((t.getRevision(t.revision - 1).hours if t.revision > 1 else 0) for t in [t2.getRevisionAt(day) for t2 in tasks] if t and t.status == 'deferred'))

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

		#TODO
		clrs = ['#4572A7', '#AA4643', '#89A54E', '#80699B', '#3D96AE', '#DB843D', '#92A8CD', '#A47D7C', '#B5CA92']

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
		clrGen = cycle(clrs)
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

		clrGen = cycle(clrs)
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
		self.plotOptions.line.dataLabels.enabled = True
		self.plotOptions.line.step = True
		self.plotOptions.line.dataLabels.x = -10
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
				'name': task.safe.name if many else 'Hours',
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
