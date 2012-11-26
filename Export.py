class SprintExport:
	def getName(self): return 'sprint'
	def getFriendlyName(self): return 'Sprint'
	def getIcon(self): return 'export-sprint'
	def getExtension(self): return 'sprints'

	def process(self, sprint):
		seps = [',', '|', ':', '~', '`']
		sep = seps[0]
		print "%s" % sep
		for group in sprint.getGroups():
			print "%s:" % group.name
			for task in group.getTasks():
				if sep in task.name:
					for sep in seps:
						if not sep in task.name:
							print "%s" % sep
							break
					else:
						raise Exception("Unable to find a valid separator for %s" % task.name)
				print sep.join([' '.join(user.username for user in task.assigned), str(task.hours), task.status, task.name])

class ExcelExport:
	def getName(self): return 'excel'
	def getFriendlyName(self): return 'Excel'
	def getIcon(self): return 'export-excel'
	def getExtension(self): return 'xls'

	def process(self, sprint): raise Exception('Unimplemented')

class FieldSeparatedExport:
	def getName(self): return 'fs'
	def getFriendlyName(self): return 'Field-separated'
	def getIcon(self): return 'export-csv'
	def getExtension(self): return 'csv'

	def process(self, sprint): raise Exception('Unimplemented')

exports = [SprintExport(), ExcelExport(), FieldSeparatedExport()]
exports = dict([(export.getName(), export) for export in exports])
