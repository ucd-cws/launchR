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

## Methods and Caveats

Currently, launchR is Windows only and finds the R install from the registry. If R wasn't installed with the setting
to put R information in the registry, launchR will not find R. R can be installed for all users or as a local user.
LaunchR will check for an all users installation first, and check for a local user installation as a backup if it can't
find a copy installed for all users