from __future__ import print_function
__version__ = "0.2.1"
__author__ = "nickrsan"

import os
import subprocess
import logging

log = logging.getLogger("launchR")
log.setLevel(logging.DEBUG)
sth = logging.StreamHandler()
sth.setLevel(logging.INFO)
log.addHandler(sth)

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


class Interpreter(object):

	def __init__(self, version=None):
		self.version = version  # set version by default to whatever was supplied
		self.executable, self.version = self._get_r_executable()  # but if nothing was supplied, get_r_executable will do it
		self.user_library = self._get_user_packages_folder()

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


	def _get_user_packages_folder(self):
		major_version, minor_version, sub_version = self.version.split(".")
		packages_version = "{}.{}".format(major_version, minor_version)  # get the version format used for packages
		new_r_package_folder = os.path.join(os.environ["USERPROFILE"], "Documents", "R", "win-library", packages_version)

		return new_r_package_folder

	def install_packages(self, package_list, library=None):
		log.info("Installing R packages using interpreter at {}. This may take some time".format(self.executable))
		if not library:  # doing this here so we can use a self variable as a default
			library = self.user_library

		if not os.path.exists(library):
			os.makedirs(library)

		package_list = ['\\"{}\\"'.format(package) for package in package_list]  # stringify and surround with single quotes
		try:  # careful with the \\ and the quoting below. Very specifically tuned to allow this command to execute outside of a script!
			self.run("-e", 'install.packages(c({}), dependencies=TRUE, lib=\\"{}\\", repos=\\"http://cran.us.r-project.org\\");'.format(", ".join(package_list), library.replace("\\", "\\\\")))
		except subprocess.CalledProcessError as e:
			raise PackageInstallError(e.returncode, e.output)

	def run(self, script, *args):
		if not "R_LIBS_USER" in os.environ:
			os.environ["R_LIBS_USER"] = self.user_library

		try:
			subprocess.check_output([self.executable, script] + list(args), stderr=subprocess.STDOUT)
		except subprocess.CalledProcessError:
			raise

