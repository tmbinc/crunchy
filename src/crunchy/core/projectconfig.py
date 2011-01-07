def parse_project_config(s):
	project_config={}

	for i in s.split(","):
		name, _, value = i.partition("=")
		assert _ == "=", "Project config syntax must be [name=value][,name=value]..."
		project_config[name] = int(value)

	return project_config
