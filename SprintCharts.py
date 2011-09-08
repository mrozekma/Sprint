from __future__ import division
from itertools import cycle

from Chart import Chart
from Task import Task
from Availability import Availability
from utils import *

class HoursChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)

		tasks = sprint.getTasks()

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.title.text = ''
		self.plotOptions.line.dataLabels.enabled = True
		self.tooltip.shared = True
		self.credits.enabled = False
		with self.xAxis as xAxis:
			xAxis.type = 'datetime'
			xAxis.dateTimeLabelFormats.day = '%a'
			xAxis.tickInterval = 24 * 3600 * 1000
			xAxis.maxZoom = 48 * 3600 * 1000
			xAxis.title.text = 'Day'
			xAxis.plotBands = [{
				'color': '#DDD',
				'from': dateToTs(datetime.now()) * 1000,
				'to': sprint.end * 1000
			}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Hours'
		self.series = seriesList = []

		series = {
			'name': 'Hours needed',
			'pointStart': sprint.start * 1000,
			'pointInterval': 24 * 3600 * 1000,
			'data': []
		}
		seriesList.append(series)

		for day in sprint.getDays():
			series['data'].append([dateToTs(day) * 1000, sum(t.hours if t else 0 for t in [t.getRevisionAt(day) for t in tasks])])

		series = {
			'name': 'Availability',
			'pointStart': sprint.start * 1000,
			'pointInterval': 24 * 3600 * 1000,
			'data': []
		}
		seriesList.append(series)

		avail = Availability(sprint)
		for day in sprint.getDays():
			series['data'].append([dateToTs(day) * 1000, avail.getAllForward(day)])

		series = {
			'name': 'Earned value',
			'pointStart': sprint.start * 1000,
			'pointInterval': 24 * 3600 * 1000,
			'data': []
		}
		seriesList.append(series)

		for day in sprint.getDays():
			series['data'].append([dateToTs(day) * 1000, sum(t.hours if t else 0 for t in [t.getRevisionAt(day) for t in tasks if t.status == 'complete'])])

		series = {
			'name': 'Deferred tasks',
			'pointStart': sprint.start * 1000,
			'pointInterval': 24 * 3600 * 1000,
			'data': []
		}
		seriesList.append(series)

		for day in sprint.getDays():
			series['data'].append([dateToTs(day) * 1000, sum(t.hours if t else 0 for t in [t.getRevisionAt(day) for t in tasks if t.status == 'deferred'])])


class HoursByUserChart(Chart):
	def __init__(self, placeholder, sprint):
		Chart.__init__(self, placeholder)

		tasks = sprint.getTasks()

		self.chart.defaultSeriesType = 'line'
		self.chart.zoomType = 'x'
		self.title.text = ''
		# self.plotOptions.line.dataLabels.enabled = True
		self.tooltip.shared = True
		self.credits.enabled = False
		with self.xAxis as xAxis:
			xAxis.type = 'datetime'
			xAxis.dateTimeLabelFormats.day = '%a'
			xAxis.tickInterval = 24 * 3600 * 1000
			xAxis.maxZoom = 48 * 3600 * 1000
			xAxis.title.text = 'Day'
			xAxis.plotBands = [{
				'color': '#DDD',
				'from': dateToTs(datetime.now()) * 1000,
				'to': sprint.end * 1000
			}]
		self.yAxis.min = 0
		self.yAxis.title.text = 'Hours'
		self.series = seriesList = []

		for user in sorted(sprint.members):
			series = {
				'name': user.username,
				'pointStart': sprint.start * 1000,
				'pointInterval': 24 * 3600 * 1000,
				'data': []
			}
			seriesList.append(series)

			userTasks = filter(lambda t: t.assigned == user, tasks)
			for day in sprint.getDays():
				series['data'].append([dateToTs(day) * 1000, sum(t.hours if t else 0 for t in [t.getRevisionAt(day) for t in userTasks])])

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
				'y': float("%2.2f" % (100 * hours / total)),
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
				'y': float("%2.2f" % (100 * hours / total)),
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
