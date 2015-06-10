# ref:
# https://www.sublimetext.com/forum/viewtopic.php?f=3&t=11292
# http://superuser.com/questions/556609/filtering-sublime-text-2-buffer-contents-through-an-external-program

import sublime, sublime_plugin, subprocess, traceback, os.path
import re

DefaulBinary = "uncrustify"

def getProgram():
	# load settings
	settings = sublime.load_settings("Uncrustify.sublime-settings")
	user_settings = sublime.load_settings("Preferences.sublime-settings")

	# get binary setting
	program = user_settings.get("uncrustify_binary") or \
			    settings.get("uncrustify_binary")
	if program:
		# only if exists
		if not os.path.exists(program):
			err = "Cannot find '%s'" % program
			sublime.error_message(err)
			return ""
	else:
		# will find uncrustify in PATH
		program = DefaulBinary

	return program

def getConfig():
	# load settings
	settings = sublime.load_settings("Uncrustify.sublime-settings")
	user_settings = sublime.load_settings("Preferences.sublime-settings")

	# get default config setting
	config = user_settings.get("uncrustify_config") or \
			 settings.get("uncrustify_config")
	if config:
		# only if exists
		if not os.path.exists(config):
			err = "Cannot find '%s'" % config
			sublime.error_message(err)
			return ""
	else:
		# try from environment variable
		config = os.getenv("UNCRUSTIFY_CONFIG", "")
		if not config:
			err = "Need to specify the config file in Uncrustify settings\nor set UNCRUSTIFY_CONFIG in OS!"
			sublime.error_message(err)
			return ""
		# only if exists
		if not os.path.exists(config):
			err = "Cannot find '%s' (from UNCRUSTIFY_CONFIG)" % config
			sublime.error_message(err)
			return ""

	return config

def getConfigByLang(lang):
	# load settings
	settings = sublime.load_settings("Uncrustify.sublime-settings")
	user_settings = sublime.load_settings("Preferences.sublime-settings")

	# get config setting
	configs = user_settings.get("uncrustify_config_by_lang", []) or \
			  settings.get("uncrustify_config_by_lang", [])

	# find one matched the language
	for each in configs:
		for key, config in each.items():
			# print(key, config)
			if key and config and lang == key:
				# only if exists
				if not os.path.exists(config):
					err = "Cannot find '%s' (for %s)" % (config, lang)
					sublime.error_message(err)
					return ""
				return config

	# just no one matched
	return "none"

def getConfigByFilter(path_name):
	# load settings
	settings = sublime.load_settings("Uncrustify.sublime-settings")
	user_settings = sublime.load_settings("Preferences.sublime-settings")

	# get config setting
	configs = user_settings.get("uncrustify_config_by_filter", []) or \
			  settings.get("uncrustify_config_by_filter", [])

	# find one appeared in path_name
	for each in configs:
		for key, config in each.items():
			# print(key, config)
			if key and config and path_name.find(key):
				# only if exists
				if not os.path.exists(config):
					err = "Cannot find '%s' (for %s)" % (config, lang)
					sublime.error_message(err)
					return ""
				return config

	# just no one matched
	return "none"

def guessLanguage(ext_name):
	if ext_name == ".c":
		return "C"
	elif ext_name == ".cpp" or \
		 ext_name == ".h" or \
		 ext_name == ".cxx" or \
		 ext_name == ".hpp" or \
		 ext_name == ".cc" or \
		 ext_name == ".cp" or \
		 ext_name == ".C" or \
		 ext_name == ".CPP" or \
		 ext_name == ".c++":
		return "CPP"
	elif ext_name == ".d" or \
		 ext_name == ".di":
		return "D"
	elif ext_name == ".cs":
		return "CS"
	elif ext_name == '.java':
		return "JAVA"
	elif ext_name == ".pawn" or \
		 ext_name == ".p" or \
		 ext_name == ".sma" or \
		 ext_name == ".inl":
		return "PAWN"
	elif ext_name == ".m":
		return "OC"
	elif ext_name == ".mm":
		return "OC+"
	elif ext_name == ".vala":
		return "VALA"
	elif ext_name == ".sql":
		return "SQL"
	elif ext_name == ".es":
		return "ECMA"

	msg = "Unknown file extension: %s" % ext_name
	sublime.message_dialog(msg)
	return ""

def getLanguage(view):
	# get topmost scope
	scope = view.scope_name(view.sel()[0].end())

 	# should be source.<lang_name>
	result = re.search("\\bsource\\.([a-z+\-]+)", scope)

	lang_name = result.group(1) if result else "Plain Text"
	# print(lang_name)
	if lang_name == "Plain Text":
		# check if match our extension names
		path = view.file_name()
		if not path:
			msg = "Unknown language: %s" % lang_name
			sublime.message_dialog(msg)
			return ""

		file_name, ext_name = os.path.splitext(path)
		return guessLanguage(ext_name)

	if lang_name == "c":
		return "C"
	elif lang_name == "c++":
		return "CPP"
	elif lang_name == "d":
		return "D"
	elif lang_name == "c#":
		return "CS"
	elif lang_name == 'java':
		return "JAVA"
	elif lang_name == "pawn":	# not listed in sublime default
		return "PAWN"
	elif lang_name == "objc":
		return "OC"
	elif lang_name == "objc++":
		return "OC+"
	elif lang_name == "vala":	# not listed in sublime default
		return "VALA"
	elif lang_name == "sql":
		return "C"
	elif lang_name == "es":		# not listed in sublime default
		return "ECMA"

	msg = "Unsupported language: %s" % lang_name
	sublime.message_dialog(msg)
	return ""

def reformat(view, edit, region):
	content = view.substr(region)
	command = []

	# assign the external program
	program = getProgram()
	if not program:
		return

	command.append(program)

	# specify the language override (because input is from stdin)
	lang = getLanguage(view)
	if not lang:
		return

	command.append("-l")
	command.append(lang)

	# specify the config file:
	# try 1
	config = getConfigByFilter(view.file_name())
	if not config:
		return
	# try 2
	if config == "none":
		config = getConfigByLang(lang)
		if not config:
			return
	# try 3
	if config == "none":
		config = getConfig()
		if not config:
			return

	command.append("-c")
	command.append(config)

	print(command)
	# MEMO:
	# command[] should like
	# ['C:/path/uncrustify.exe', '-l', 'CPP', '-c', 'C:/path/ob.cfg']

	try:
		# run
		proc = subprocess.Popen(command, \
			   stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		output = proc.communicate(input=content.encode("utf-8"))[0]

		# wait return
		return_code = proc.poll()
		if return_code != 0:
			stderr = proc.communicate()[1]
			if stderr:
				err = "Found error in executing '%s':\n\n%s" % (command[0], stderr.decode("utf-8"))
			else:
				err = "Found error in executing '%s':\n\nCode %d" % (command[0], return_code)
			sublime.error_message(err)
			return

		# print(output)

		# replace by result
		view.replace(edit, region, output.decode("utf-8"))

	except (OSError, ValueError, subprocess.CalledProcessError, Exception) as e:
		# traceback.print_exc()
		if command[0] == DefaulBinary:
			err = "Cannot execute '%s' (from PATH)\n\n%s" % (command[0], e)
		else:
			err = "Cannot execute '%s'\n\n%s" % (command[0], e)
		sublime.error_message(err)

def open_file(window, file_name):
	window.open_file(file_name)

# Uncrustify the document
class UncrustifyDocumentCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		# make full view as region
		region = sublime.Region(0, self.view.size())
		if region.empty():
			# sublime.message_dialog("Empty document!")
			sublime.status_message("Empty document!")
			return

		# go
		reformat(self.view, edit, region)

# Uncrustify only the selection region
class UncrustifySelectionCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		# get selections
		sel = self.view.sel()

		# pick 1st selection as region
		# TODO: try to support multi-selection...
		# for region in self.view.sel():
		# 	...
		region = sel[0]
		if region.empty():
			sublime.message_dialog("No selection!")
			return

		# go
		reformat(self.view, edit, region)

# open the config file to edit
class UncrustifyOpenCfgCommand(sublime_plugin.WindowCommand):
	def run(self):
		config = getConfig()
		if not config:
			return

		# go
		open_file(self.window, config)


# open the config file which matches current document to edit
class UncrustifyOpenCfgCurrentCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		# get the language
		lang = getLanguage(self.view)
		if not lang:
			return

		# specify the config file:
		# try 1, if matches one of filters
		config = getConfigByFilter(self.view.file_name())
		if not config:
			return
		# try 2, if matches one of languages
		if config == "none":
			config = getConfigByLang(lang)
			if not config:
				return
		# try 3, use default
		if config == "none":
			config = getConfig()
			if not config:
				return

		# go
		open_file(sublime.active_window(), config)
