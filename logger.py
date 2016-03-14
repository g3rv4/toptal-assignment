from logging import basicConfig, getLogger, DEBUG

basicConfig(format='%(asctime)s %(name)-40s %(lineno)-3s %(levelname)-8s %(message)s')
getLogger().setLevel(DEBUG)
