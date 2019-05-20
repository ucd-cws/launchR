from __future__ import print_function
__version__ = "0.3.0"
__author__ = "nickrsan"

import os
import subprocess
import logging
import tempfile

log = logging.getLogger("launchR")
log.setLevel(logging.DEBUG)
sth = logging.StreamHandler()
sth.setLevel(logging.INFO)
log.addHandler(sth)
fih = logging.FileHandler(tempfile.mktemp("launchR_log"))
fih.setLevel(logging.DEBUG)
log.addHandler(fih)

try:
	import winreg
except ImportError:
	import _winreg as winreg


class PackageInstallError(SystemError):
	def __init__(self, return_code, message, **kwargs):
		self.return_code = return_code
		self.message = message
		super(PackageInstallError, self).__init__(**kwargs)

	def __str__(self):
		log.error("Installation of R packages failed {}.\nR Package installer output the following while processing:\n{}".format(self.return_code, self.message))


class RExecutionError(SystemError):
	def __init__(self, return_code, message, **kwargs):
		self.return_code = return_code
		self.output = message
		super(RExecutionError, self).__init__(**kwargs)

	def __str__(self):
		log.error("Execution of R script failed with return code {}.\nR output the following while processing:\n{}".format(self.return_code, self.output))


class Interpreter(object):

	def __init__(self, version=None):
		self.version = version  # set version by default to whatever was supplied
		self.executable, self.version = self._get_r_executable()  # but if nothing was supplied, get_r_executable will do it
		self.user_library = self._get_user_packages_folder()
		self.packages = {}  # we'll add an entry here if we check for an installed package - keys are names, map to true or false if it's there

	def _get_versions_from_reg(self, base_key=winreg.HKEY_LOCAL_MACHINE):
		"""

		:param base_key:
		:param version:
		:return:
		"""
		registry = winreg.ConnectRegistry("", base_key)  # open the registry
		try:
			if self.version:
				append = "\\{}".format(self.version)
			else:
				append = ""
			open_key = r"Software\R-core\R{}".format(append)

			key = winreg.OpenKey(registry, open_key)  # append on a version specific path if provided
			r_path = winreg.QueryValueEx(key, "InstallPath")[0]

			if self.version:
				r_version = self.version  # return the version passed in
			else:  # if no version passed in, retrieve it from the registry
				r_version = winreg.QueryValueEx(key, "Current Version")[0]
		finally:
			winreg.CloseKey(registry)

		return r_path, r_version


	def _get_r_executable(self):
		"""
			We make this a function and call it first because setuptools just puts "error:none" if it errors out inside the
			main setup call. So, check before doing any other installation, which seems like a good idea anyway.
		:return:
		"""
		try:
			current_r_path, current_r_version = self._get_versions_from_reg(base_key=winreg.HKEY_LOCAL_MACHINE)
		except WindowsError:
			try:
				current_r_path, current_r_version = self._get_versions_from_reg(base_key=winreg.HKEY_CURRENT_USER)
			except WindowsError:
				if self.version:
					raise WindowsError("Unable to find the specified version of R in the registry")
				raise WindowsError("Unable to get R path - Make sure R is installed on this machine!")

		log.info("R located at {}".format(current_r_path))

		return os.path.join(current_r_path, "bin", "Rscript.exe"), current_r_version


	def _get_documents_folder_from_reg(self):
		"""
			Originally, we used the USERPROFILE environment variable, but in early testing, found an issue with a user
			who had his Documents folder redirected to another drive, with USERPROFILE still in the same spot. So, when
			we constructed the user packages folder path, we were in the wrong location (R seems to pick up the folder
			redirection correctly, which is good). So, we pull the documents folder location from the registry here.
		:return: path to user's documents folder
		"""

		registry = winreg.ConnectRegistry("", winreg.HKEY_CURRENT_USER)  # open the registry
		try:
			open_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"  # http://stackoverflow.com/questions/3492920/is-there-a-system-defined-environment-variable-for-documents-directory

			key = winreg.OpenKey(registry, open_key)  # append on a version specific path if provided
			documents_path = winreg.QueryValueEx(key, "Personal")[0]
		finally:
			winreg.CloseKey(registry)

		return documents_path

	def _get_user_packages_folder(self):
		major_version, minor_version, sub_version = self.version.split(".")
		packages_version = "{}.{}".format(major_version, minor_version)  # get the version format used for packages
		new_r_package_folder = os.path.join(self._get_documents_folder_from_reg(), "R", "win-library", packages_version)

		return new_r_package_folder

	def _package_install(self, package_list, library, install_command="install.packages", extra_args=None):
		log.info("Installing R packages using interpreter at {}. This may take some time".format(self.executable))
		if not library:  # doing this here so we can use a self variable as a default
			library = self.user_library

		if not os.path.exists(library):
			os.makedirs(library)

		package_list = ['\\"{}\\"'.format(package) for package in package_list]  # stringify and surround with single quotes
		try:  # careful with the \\ and the quoting below. Very specifically tuned to allow this command to execute outside of a script!
			run_string = '{}(c({}), lib=\\"{}\\");'.format(install_command, ", ".join(package_list), library.replace("\\", "\\\\"))
			if extra_args:
				run_string = "{}, {});".format(run_string[:-2], extra_args)  # strip the last two characters off the old one, then insert the args and add the last two characters back
			self.run("-e", run_string)
		except subprocess.CalledProcessError as e:
			raise PackageInstallError(e.returncode, e.output)

	def _check_packages_installed(self, package_list):
		"""
			Checks if the packages named in the Python list package_list are installed in the R interpreter
		:param package_list: 
		:return: 
		"""
		for package in package_list:
			if package in self.packages:  # skip it if we've already checked
				continue

			try:
				self.run('-e', "library({})".format(package))
				self.packages[package] = True
			except RExecutionError:
				self.packages[package] = False

	def check_packages(self, package_list):
		"""
			
		:param package_list: 
		:return: 
		"""
		self._check_packages_installed(package_list)

		for package in package_list:
			if package not in self.packages or self.packages[package] is False:
				return False

	def install_packages(self, package_list, library=None, missing_only=True):
		"""
			Given a list of packages, installs those packages to the specified user library, or the default user library
		:param package_list: 
		:param library: 
		:param missing_only: Only installs packages that aren't yet in the library
		:return: 
		"""

		install_packages = []
		if missing_only:  # if we're only supposed to install the missing ones, then check which ones are installed, and add the missing ones to a new list
			self._check_packages_installed(package_list)
			for package in package_list:
				if package not in self.packages or self.packages[package] is False:
					install_packages.append(package)

			if len(install_packages) == 0:  # do we have things to install?
				return
			package_list = install_packages  # set the package list to install again

		extra_args = 'dependencies=TRUE, repos=\\"http://cran.us.r-project.org\\"'
		self._package_install(package_list, library, install_command="install.packages", extra_args=extra_args)

	def install_github(self, package_list, library=None):
		"""
			Given a list of github package names (username/repository) format, installs the packages
		:param package_list: 
		:param library: 
		:return: 
		"""
		self.install_packages(["devtools"], library=library, missing_only=True)  # install devtools if it's missing from the library

		self._package_install(package_list, library, install_command="library(devtools);devtools::install_github")  # then call the install_github command

	def run(self, script, *args):
		"""
			Executes the script provied and makes everything in args available sequentially as command line arguments
		"""
	
		if not "R_LIBS_USER" in os.environ:
			os.environ["R_LIBS_USER"] = self.user_library

		CREATE_NO_WINDOW = 0x08000000  # used to hide a created console window (in the event of using an embedded Python interpreter) so it stays in the background
		try:
			subprocess.check_output([self.executable, script] + list(args), creationflags=CREATE_NO_WINDOW, stderr=subprocess.STDOUT)
		except subprocess.CalledProcessError as e:
			raise RExecutionError(e.returncode, e.output)


