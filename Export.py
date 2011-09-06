class SprintExport:
	def getName(self): return 'sprint'
	def getFriendlyName(self): return 'Sprint'
	def getIcon(self): return 'export-sprint'
	def getExtension(self): return 'sprints'

	def process(self, sprint): raise Exception('Unimplemented')

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
