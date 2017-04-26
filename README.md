# launchR - simple R code execution from Python

launchR finds your R installation and provides convenience functions for running R scripts from Python, including
package installation and running scripts. Currently, error output will be displayed in your Python script,
but normal output may not.

## Installation

To install launchR, simply call `pip install launchR`

## Examples
```python
import launchR
R = launchR.Interpreter()  # by default, finds R using the 
R.install_packages(["dplyr", "Rcpp"])  # raises launchR.PackageInstallError on failure
R.run("full\\path\\to\\my_script.R", "--args", "argument1", "argument2",)  # raises launchR.RExecutionError on failure
print(R.version)  # the R version found in the registry for the current interpreter
```

Or alternatively, if you are trying to use a specific version
```python
# get a specific version of the interpreter, if installed
R = launchR.Interpreter(version="3.3.2")  # raises WindowsError if it can't be found
print(R.executable)  # prints the path to the found executable
print(R.user_library)  # prints the path to the user packages folder
```

Check for a specific package
```python
R.check_packages(["devtools"])  # returns True if installed, False otherwise. When providing more than one package, returns True only if all are installed
```

Install packages only if they aren't installed already
```python
R.install_packages(["devtools", "dplyr",], missing_only=True)  # True is the default

# Once check_packages or install_packages with missing_only==True has been run, we can just check R.packages["package_name"] for a True/False
if R.packages["devtools"] == True:
	pass  # do something here
```

Install from GitHub
```python
# uses devtools::install_github to install packages from GitHub - uses the same organization/repository format for installation
packages = ["organization/repository1", "organization2/repository1"] 
R.install_github(packages)  # automatically confirms that devtools is installed and installs it if it's missing
```


## Methods and Caveats

Currently, launchR is Windows only and finds the R install from the registry. If R wasn't installed with the setting
to put R information in the registry, launchR will not find R. R can be installed for all users or as a local user.
LaunchR will check for an all users installation first, and check for a local user installation as a backup if it can't
find a copy installed for all users

## Changelog
 * 0.3.0 Added install_github to install packages from github using devtools, and check_packages for determining if packages are installed. Also added flag to install_packages named missing_only (True by default), which causes the installer to only install packages if it knows them to be missing already (can save time in some cases)
 * 0.2.5 Made RExecutionError have returncode and output attributes similar to CalledProcessError
 * 0.2.4 Changed user library lookup to use the registry to account for redirected documents folders
 * 0.2.3 Added RExecutionError to be caught when running R fails
 * 0.2.1-0.2.2 Bugfixes
 * 0.2.0 Initial release