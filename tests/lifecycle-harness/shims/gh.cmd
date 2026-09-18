@echo off
rem Windows shell callers. Python callers need gh.exe - see env.py:_install_shims.
python "%~dp0gh_shim.py" %*
