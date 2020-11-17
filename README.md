# projector-installer
[![JetBrains incubator project](https://jb.gg/badges/incubator.svg)](https://confluence.jetbrains.com/display/ALL/JetBrains+on+GitHub)
![Python 3.6+](https://img.shields.io/badge/Python-3.6+-blue.svg)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![PyLint/MyPy Runner](https://github.com/JetBrains/projector-installer/workflows/PyLint/MyPy%20Runner/badge.svg)

Install, configure and run JetBrains IDEs with [Projector Server](https://github.com/JetBrains/projector-server/blob/master/docs/Projector.md) on Linux or in [WSL](https://docs.microsoft.com/windows/wsl/).

[Latest release](https://pypi.org/project/projector-installer/) | 
[Sources](https://github.com/JetBrains/projector-installer) | 
[Changelog](https://github.com/JetBrains/projector-installer/blob/master/CHANGELOG.md)


# Table of Contents
1. [Installation](#Installation)
2. [Quick start](#Quick-start)
3. [FAQ](#FAQ)

## Installation
### Prerequisites
To use projector-installer you need machine with Linux (or WSL) and with Python 3.6 or higher.
Before install projector-installer make sure that you have python3 and pip3 installed in your system. 
In Debian-based distributive you can install them using the command:
```bash
sudo apt install python3 python3-pip 
``` 
Also make sure that you have installed the following packets: 
 - libxext6
 - libxi6
 - libxrender1
 - libxtst6
 - libfreetype6
   
In Debian-based distributive you can install them using the command:
```bash
sudo apt install libxext6 libxrender1 libxtst6 libfreetype6 libxi6  
```    

### Install from PyPi

You can install projector-installer script from PyPi, using command: 

```bash
pip3 install projector-installer 
```

After that the command `projector` should be available. 

_NOTE:_ If it is not so, please refer to the [appropriate section](#no_projector) in the [FAQ](#FAQ).

_NOTE:_ projector script checks for updates on start. 
If new version is available you can install update using command 
`pip3 install projector-installer --upgrade`   

## Quick start 
First time you run projector, it will automatically download, install, configure 
and start IDE. Just run projector and follow the instructions. 
The script will run the installed IDE with projector-server and display URLs to access it. 
Open an URL in your browser and use IDE as usual. 

To run IDE again use `projector run`

To install a new IDE run `projector install` 

To find out which JetBrains IDE are supported run `projector find`

To get help projector commands run `projector --help`

If you want to know more on projector usage please refer to 
[this](https://github.com/JetBrains/projector-installer/blob/master/COMMANDS.md) file.

## FAQ
### What is secure connection?
During installation Projector asks the user if they want to use a secure 
connection. If the user chooses "yes", installer configures Projector to 
use HTTPS for accessing a built-in HTTP server and WSS to communicate 
with the Projector server. Using a secure connection may be a good idea 
because some JavaScript features are not available in insecure environments, 
for example, [Asynchronous Clipboard API](https://w3c.github.io/clipboard-apis/#async-clipboard-api). 
So using Projector with insecure protocols may limit its functionality.

However, using a secure connection requires telling the browser that it should trust the certificate. 
One of the ways to do it is to do it forcefully. 
Open the page, see the warning about unknown certificate, find a button like "trust it anyway", and click it. 
After it, you will probably get a message like "can't connect to wss://host:port". 
Please change wss to https, open it in a new tab, and click the "trust" button too. 
After performing these two actions, the browser should remember this connection and 
you won't have to perform these actions again. 
Just open the initial web page and use all functionality of Projector.

### Where does projector-installer keep downloaded IDE and run configurations?
All the necessary stuff is kept in the configuration directory. Usually 
configuration directory is ~/.projector. But the user can specify 
another location for it, using option --config-directory, for example: 
`projector --config-directory=config run`

### What about Android Studio support?
Projector installer can't support automatic Android Studio installation due to 
legal issues. However installer can help you to configure already installed Android Studio 
to use with Projector. To make new run config for Android Studio use `projector config add` 
command.

_NOTE:_ Please take into account, that Projector uses JVM, bundled with IDE and supports Java 11 only.
Most of Android Studio IDE shipped with Java 1.8, so they are incompatible with Projector. 
However, starting from version 4.2 (still in EAP), Google ships Java 11 with Android Studio. 
So Android Studio ver. 4.2 and later can be run with projector.  


Example:
```bash
$projector config add
Enter a new configuration name: AndroidStudio
Do you want to choose a Projector-installed IDE? [y/n]: n
Enter the path to IDE: /path/to/your/android-studio
Enter a desired Projector port (press ENTER for default) [10005]: 
Use secure connection (this option requires installing a projector's certificate to browser)? [y/n]: y
```

### projector command is unavailable after installation
<a name="no_projector"/>

By default pip3 installs `projector` script in directory `~/.local/bin`.
If system can't find the script after installation it means that the directory 
`~/.local/bin` was not included in the _PATH_ environment variable. Try the following:
 - Restart the terminal. If `projector` was the first executable installed in `~/.local/bin`, 
 and the directory wasn't exist when your login session started, it may help.  
 
 - In some Linux distributions the directory `~/.local/bin` not included in the `PATH` 
 environment variable. In this case add `export  PATH=${PATH}:~/.local/bin` to your `~/.profile`  
 and run `source ~/.profile`.

### On WSL I can't access URL displayed in projector console from Windows browser

WSL is new technology and sometimes there are problems with network interfaces forwarding from 
Linux to Windows system. For example: https://github.com/microsoft/WSL/issues/4636 .


If you have issues with accessing Projector running in WSL from browser, try do the following:

 - Do not use several WSL machines in the same time. Connectivity issues happens rarely if only one 
 WSL machine is running. You can check state of existing WSL machies using `wsl -l -v` command.

 - Try command `Get-Service LxssManager | Restart-Service` in PowerShell console
 
  - Restart your WSL environment:
 ```wsl --shutdown```
 and start your linux console again. 
 
 *WARNING!* The `wsl --shutdown` command will close all Linux consoles. 
 Save your work before stopping WSL!
 
 - Using docker service with WSL2 backend can cause connectivity issues. 
 Try to disable it and restart WSL terminal.
 
 - Use address other than localhost.
 Usually WSL have problems forwarding localhost interface only. 
 Try to use listening address other than localhost.
 You can assign HTTP listening address during initial installation or using 
 `projector config edit` command. 
  
### projector exits immediately after `projector run`
Make sure, that you installed all packages, mentioned in [Prerequisites](#Prerequisites) section.     
