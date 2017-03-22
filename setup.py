from setuptools import setup

from launchR import __version__, __author__

setup(name="launchR",
	version=__version__,
	description="launchR finds your R installation and provides convenience functions for running R scripts from Python, including package installation and running scripts.",
	long_description="Documentation and examples can be found at https://github.com/ucd-cws/launchR ",
	packages=['launchR', ],
	author=__author__,
	author_email="nrsantos@ucdavis.edu",
	url='https://github.com/ucd-cws/launchR',
)
