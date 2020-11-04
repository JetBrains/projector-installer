# projector-installer
[![JetBrains incubator project](https://jb.gg/badges/incubator.svg)](https://confluence.jetbrains.com/display/ALL/JetBrains+on+GitHub)
![PyLint/MyPy Runner](https://github.com/JetBrains/projector-installer/workflows/PyLint/MyPy%20Runner/badge.svg)

Install, configure and run JetBrains IDEs with [Projector](https://github.com/JetBrains/projector-server/blob/master/docs/Projector.md) Server on Linux or in [WSL](https://docs.microsoft.com/windows/wsl/).

## Prerequisites
To use projector-installer you need machine with Linux (or WSL) and with Python 3.6 or higher.
Before install projector-installer make sure that you have python3 and pip3 in your system. 
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

## Installation

### install from PyPi
```bash
pip3 install projector-installer 
```

### install from wheel file 
```bash
pip3 install projector_installer-VERSION-py3-none-any.whl
```
### install from source 
```bash 
git clone https://github.com/JetBrains/projector-installer.git
cd projector-installer
pip3 install -r requirements.txt 
python3 setup.py bundle
pip3 install .
```

### install in virtual environment
```commandline
python3 -m venv venv
source ./venv/bin/activate 
pip3 install  projector-installer 
``` 

After that the command `projector` is available. 

_NOTE:_ In fresh Linux installations the directory ```~/.local/bin```
can be missed in the ```PATH``` variable. If the ```projector``` command
is not available after installation, try to restart the terminal.


## Quick start 
First time you run projector, it automatically starts the installation.
Just run projector and follow the instructions. 
The script will run the installed IDE with projector-server and display URL to access it. 
Open this URL in your browser and use IDE as usual.

To run IDE again use _projector run_

To install a new IDE run _projector install_ 

## Get help 
General help: ```projector --help```:
 
Command or command group help: ```projector  command --help```:
```bash
projector run --help

projector config --help
```

Subcommand help: ```projector  group subcommand --help``` to get help.

```bash
projector config add --help
```

### Shortcut commands

To simplify usage most useful commands have shortcuts. In simple cases 
(when you have the only IDE installed, or you do not run several IDE instances simultaneously) 
it is enough to use a couple of shortcut commands, such as install and run.

- find  - find available IDEs (a shortcut for 'ide find')
 
- install - install IDE (a shortcut for 'ide install')

- run - run IDE (a shortcut for 'config run')


## Details 

Script has two groups of commands:

- IDE management commands intended to manage Projector-compatible IDEs.
  All such commands are prefixed with 'ide' keyword, for example:
    
    ```bash
    projector ide find 
    ``` 
   
finds all Projector-compatible IDEs. 
 
or:

```bash
   projector ide find goland
``` 
 
finds all Projector-compatible IDEs which have 'goland' in their names.

- config commands, intended to run and manage _configurations_, for example:
    ```bash 
    projector config run goland
   ``` 
    
runs the configuration with name 'goland'


### IDE commands
`projector ide find` - display all Projector-compatible IDEs

`projector ide find pattern` - display Projector-compatible IDEs whose names match the given pattern

`projector ide list` - display all installed IDEs

`projector ide list pattern` - display Projector-compatible IDEs whose names match the given pattern

`projector ide install` - select and install IDE interactively
 
`projector ide install ide_name` - install the specified IDE

`projector ide uninstall` - uninstall IDE interactively 

`projector ide uninstall ide_name` - uninstall the specified IDE 

### Config commands 
`projector config run` - run default or interactively selected configuration with Projector
 
`projector config run configuration` - run the specified configuration

`projector config list` - list all existing configurations
 
`projector config add` - add a new configuration

`projector config edit` - change an existing configuration

`projector config edit configuration` - change the specified configuration

`projector config remove` - select configuration and remove it 

`projector config remove config_name` - remove a configuration

`projector config rename from_config_name to_config_name` - rename an existing configuration

`projector config show` - show configuration details

`projector config rebuild` - regenerates all files, related to run config. 
Can be useful after manual run config file edit, or incompatible changes in installer. 

### Configuration options
Projector installer script has the following configuration options:

--config-directory=path_to_dir - specifies path to [configuration directory](#config_dir). Default - ~/.projector

--cache-directory=path_to_dir - specifies path to download cache directory. 

## Build python wheel file
```bash
pip3 install wheel
rm -r projector_installer/bundled dist build  # Remove old build files
python3 setup.py bundle bdist_wheel
```

## Publish
```shell script
rm -r projector_installer/bundled dist build  # Remove old build files
python3 setup.py bundle sdist bdist_wheel  # Build required files
python3 -m twine upload --repository testpypi --verbose dist/*  # Upload to https://test.pypi.org/project/projector-installer/
python3 -m twine upload dist/*  # Upload to https://pypi.org/project/projector-installer/
```

## Secure connection

During installation Projector asks the user if they want to use a secure 
connection. If the user chooses "yes", installer configures Projector to 
use HTTPS for accessing a built-in HTTP server and WSS to communicate 
with the Projector server. Using a secure connection may be a good idea 
because some JavaScript features are not available in insecure environments, 
for example, [Asynchronous Clipboard API](https://w3c.github.io/clipboard-apis/#async-clipboard-api). 
So using Projector with insecure protocols may limit its functionality.

However, using a secure connection requires telling the browser that it should trust the certificate. One of the ways to do it is to do it forcefully. Open the page, see the warning about unknown certificate, find a button like "trust it anyway", and click it. After it, you will probably get a message like "can't connect to wss://host:port". Please change wss to https, open it in a new tab, and click the "trust" button too. After performing these two actions, the browser should remember this connection and you won't have to perform these actions again. Just open the initial web page and use all functionality of Projector.

## FAQ
<a name="config_dir"></a>
1. Where does projector-installer keep downloaded IDE and run configurations?

All the necessary stuff is kept in the configuration directory. Usually 
configuration directory is ~/.projector. But the user can specify 
another location for it, using option --config-directory, for example: 
`projector --config-directory=config run`


## Android Studio support
Projector installer can't support automatic Android Studio installation due to 
legal issues. However installer can help you to configure existing Android Studio 
installation to use with Projector. To  make new run config for Android Studio 
use `projector config add` command.


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

## Troubleshooting
- `projector` command is unavailable after installation.

In some Linux distributions the directory `~/.local/bin`
can be missed in the `PATH` variable. If the `projector` command
is not available after installation, try run `source ~/.profile`.
If it does not help, try add the following line at the end of your ~/.profile:
`export  PATH=${PATH}:~/.local/bin` and run `source ~/.profile`.

- On WSL can't access URL, displayed in projector console from Windows browser.

Please refer to section [Resolving WSL issues](#Resolving-WSL-issues).

- projector exits immediately after `projector run`

Make sure, that you installed all packages, mentioned in [Prerequisites](#Prerequisites) section.     

## Resolving WSL issues
WSL is new technology and sometimes there are problems with network interfaces forwarding from Linux to Windows system.
(Example: https://github.com/microsoft/WSL/issues/4636)

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
 
 - Use HTTP address other than localhost.
 Usually WSL have problems forwarding localhost interface only. 
 Try to use listening address other than localhost.
 You can assign HTTP listening address during initial installation or using 
 `projector config edit` command. 
 
 *WARNING!* Using external address for projector HTTP server can be dangerous, 
 use this method with caution.   
   
