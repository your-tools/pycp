@echo off
rem Make sure the script will be executed with the same
rem Python it was installed for.
set path=%~dp0;%~dp0..;%path%
python -c "import pycp; pycp.main('copy')" %*
