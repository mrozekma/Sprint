from __future__ import division
from itertools import cycle

from Chart import Chart
from Task import Task
from Availability import Availability
from utils import *

def setupTimeline(chart, sprint):
	chart.tooltip.formatter = """
function() {
	rtn = '<span style="font-size: 7pt">' + this.points[0].point.name + '</span><br>';
	this.points.forEach(function(point) {
		rtn += '<span style="color: ' + point.series.color + '">' + point.series.name + '</span>: <b>' + point.y + '</b><br>';
	});
	return rtn;
}
"""
	chart.xAxis.categories = [day.strftime('%a') for day in sprint.getDays()]
	chart.series[0].data = [[a, b] for (a, b) in zip([day.strftime('%A, %b %d, %Y') for day in sprint.getDays()], chart.series[0].data.get())]

class HoursChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)

		tasks = sprint.getTasks()

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
			if futureStarts:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': days.index(futureStarts),
					'to': len(days) - 1
				}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Hours'
		self.series = seriesList = []

		series = {
			'name': 'Hours needed',
			'data': []
		}
		seriesList.append(series)

		for day in days:
			series['data'].append(sum(t.hours if t else 0 for t in [t.getRevisionAt(day) for t in tasks]))

		series = {
			'name': 'Availability',
			'data': []
		}
		seriesList.append(series)

		avail = Availability(sprint)
		for day in days:
			series['data'].append(avail.getAllForward(day))

		setupTimeline(self, sprint)

		

class EarnedValueChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)
		days = [day for day in sprint.getDays()]
		now = getNow()
		futureStarts = minOr(filter(lambda day: day > now, days), None)

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
			if futureStarts:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': days.index(futureStarts),
					'to': len(days) - 1
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
			series['data'].append(sum(tOrig.hours for (tOrig, tNow) in [(t.getRevisionAt(tsToDate(sprint.start)), t.getRevisionAt(day)) for t in tasks] if tOrig and tNow and tNow.status == 'complete'))

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

		tasks = sprint.getTasks()

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.title.text = ''
		self.tooltip.shared = True
		self.credits.enabled = False
		with self.xAxis as xAxis:
			xAxis.tickmarkPlacement = 'on'
			xAxis.maxZoom = 1
			xAxis.title.text = 'Day'
			if futureStarts:
				xAxis.plotBands = [{
					'color': '#DDD',
					'from': days.index(futureStarts),
					'to': len(days) - 1
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

			userTasks = filter(lambda t: t.assigned == user, tasks)
			for day in days:
				series['data'].append(sum(t.hours if t else 0 for t in [t.getRevisionAt(day) for t in userTasks]))

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

		originalTasks = Task.loadAll(sprintid = sprint.id, revision = 1)
		clrGen = cycle(clrs)
		total = sum(t.hours for t in originalTasks)
		for user in sorted(sprint.members):
			hours = sum(t.hours for t in originalTasks if t.assignedid == user.id)
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
			hours = sum(t.hours for t in tasks if t.assignedid == user.id)
			series['data'].append({
				'name': user.username,
				'x': hours,
				'y': float("%2.2f" % (100 * hours / total if total > 0 else 0)),
				'color': clrGen.next()
			})

class SprintGoalsChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)

		tasks = sprint.getTasks()
		start = tsToDate(sprint.start)

		self.chart.defaultSeriesType = 'bar'
		self.title.text = ''
		self.tooltip.formatter = "function() {return '<b>' + this.series.name + '</b>: ' + this.point.y + '%';}"
		self.credits.enabled = False
		self.xAxis.categories = [' ']
		self.xAxis.title.text = 'Goals'
		self.yAxis.min = 0
		self.yAxis.max = 100
		self.yAxis.title.text = 'Percent complete'
		self.series = seriesList = []

		originalTasks = Task.loadAll(sprintid = sprint.id, revision = 1)
		taskMap = dict([(task.id, task) for task in tasks])
		for goal in sprint.getGoals() + [None]:
			if goal and goal.name == '':
				continue
			start = sum(t.hours for t in originalTasks if t.id in taskMap and taskMap[t.id].goalid == (goal.id if goal else 0))
			now = sum(t.hours for t in tasks if t.goalid == (goal.id if goal else 0))
			pcnt = (start-now) / start if start > 0 and start > now else 0

			seriesList.append({
				'name': goal.name if goal else 'Other',
				'data': [float("%2.2f" % (100*pcnt))],
				'dataLabels': {'enabled': True}
			})

class TaskChart(Chart):
	def __init__(self, placeholder, tasks):
		Chart.__init__(self, placeholder)

		many = isinstance(tasks, list)
		if not many:
			tasks = [tasks]
		if len(set(task.sprint for task in tasks)) > 1:
			raise Exception("All tasks must be in the same sprint")

		sprint = tasks[0].sprint

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

			hoursByDay = dict((utcToLocal(tsStripHours(rev.timestamp)) * 1000, rev.hours) for rev in revs)
			if task.status != 'complete':
				hoursByDay[utcToLocal(tsStripHours(min(dateToTs(getNow()), sprint.end))) * 1000] = task.hours
			for pair in hoursByDay.items():
				series['data'].append(pair)
