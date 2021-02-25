# projector-installer

[![JetBrains incubator project](https://jb.gg/badges/incubator.svg)](https://confluence.jetbrains.com/display/ALL/JetBrains+on+GitHub)
![Python 3.6+](https://img.shields.io/badge/Python-3.6+-blue.svg)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![PyLint/MyPy Runner](https://github.com/JetBrains/projector-installer/workflows/PyLint/MyPy%20Runner/badge.svg)

Install, configure and run JetBrains IDEs
with [Projector Server](https://github.com/JetBrains/projector-server/blob/master/docs/Projector.md) on Linux or
in [WSL](https://docs.microsoft.com/windows/wsl/).

[Latest release](https://pypi.org/project/projector-installer/) |
[Sources](https://github.com/JetBrains/projector-installer) |
[Changelog](https://github.com/JetBrains/projector-installer/blob/master/CHANGELOG.md)

# Table of Contents

1. [Installation](#Installation)
2. [Quick start](#Quick-start)
3. [FAQ](#FAQ)
    1. [Secure connection](#Secure-connection)
    2. [projector-installer config directory](#projector-installer-config-directory)
    3. [Android Studio support](#Android-Studio-support)
    4. [projector command is unavailable](#projector-command-is-unavailable)
    5. [WSL issues](#WSL-issues)
    6. [projector exits immediately](#projector-exits-immediately)
    7. [Using Projector as systemd service](#Using-Projector-as-systemd-service)

## Installation

### Prerequisites

To use projector-installer you need machine with Linux (or WSL) and with Python 3.6 or higher. Before install
projector-installer make sure that you have python3 and pip3 installed in your system. In Debian-based distributive you
can install them using the command:

```bash
sudo apt install python3 python3-pip 
``` 

If you are running Ubuntu 18.04 or earlier update pip using the following command:

```bash
python3 -m pip install -U pip 
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
pip3 install projector-installer --user 
```

After that the command `projector` should be available.

_NOTE:_ If it is not so, please refer to the [appropriate section](#no_projector) in the [FAQ](#FAQ).

_NOTE:_ projector script checks for updates on start. If new version is available you can install an update using
command
`pip3 install projector-installer --upgrade --user`

## Quick start

First time you run projector, it will automatically download, install, configure and start IDE. Just run projector and
follow the instructions. The script will run the installed IDE with projector-server and display URLs to access it. Open
an URL in your browser and use IDE as usual.

To run IDE again use `projector run`

To install a new IDE run `projector install`

To find out which JetBrains IDE are supported run `projector find`

To get help projector commands run `projector --help`

If you want to know more on projector usage please refer to
[this](https://github.com/JetBrains/projector-installer/blob/master/COMMANDS.md) file.

## FAQ

### Secure connection

__SECURITY WARNING:
Keep your projector config directory safe when using domain certificate and private key!
Do not share its content with anybody!__

Installer is able to make run config use HTTPS for accessing a built-in HTTP server and WSS to communicate with the
Projector server. Using a secure connection may be a good idea because some JavaScript features are not available in
insecure environments, for example:
[Asynchronous Clipboard API](https://w3c.github.io/clipboard-apis/#async-clipboard-api). So using Projector with
insecure protocols may limit its functionality.

To enable this feature user should modify existing run config with install-certificate command.

There are several options:

1. Use certificate for the domain signed by known certification center. For this case use command:

``` 
projector install-certificate config_name --certificate /path/to/cert.pem --key /path/to/privatekey.pem
```

In rare cases this command may fail, if installer is not able to obtain full certificate chain. In this case user should
provide intermediate certificate chain explicitly, using command

``` 
projector install-certificate config_name --certificate /path/to/cert.pem --key /path/to/privatekey.pem --chain /path/to/chain.pem
```

*Note:* Do not forget to use domain name or IP address, included to certificate to access Projector.

2. Use self-signed certificate. For this scenario use command:

``` 
projector install-certificate config_name --certificate /path/to/cert.pem --key /path/to/privatekey.pem
```

Do not forget to add the certificate to your browser if it was not done before.

3. Instruct the installer to autogenerate certificate for you. For this scenario, just don't include certificate and key
   files to install-certificate command:

``` 
projector install-certificate config_name
```

Using a secure connection with autogenerated certificate requires telling the browser that it should trust the
certificate. One of the ways to do it is to do it forcefully. Open the page, see the warning about unknown certificate,
find a button like "trust it anyway", and click it. After it, you will probably get a message like "can't connect to
wss://host:port". Please change wss to https, open it in a new tab, and click the "trust" button too. After performing
these two actions, the browser should remember this connection and you won't have to perform these actions again. Just
open the initial web page and use all functionality of Projector.

### projector-installer config directory

projector-installer keeps downloaded IDE and run configurations in the configuration directory. Usually configuration
directory is ~/.projector. User can specify another location for it, using option --config-directory, for example:
`projector --config-directory=config run`

### Android Studio support

Projector installer can't support automatic Android Studio installation due to legal issues. However, installer can help
you to configure already installed Android Studio to use with Projector. To make new run config for Android Studio
use `projector config add`
command.

_NOTE:_ Please take into account, that Projector uses JVM, bundled with IDE and supports Java 11 only. Most of Android
Studio IDE shipped with Java 1.8, so they are incompatible with Projector. However, starting from version 4.2 (still in
EAP), Google ships Java 11 with Android Studio. So Android Studio ver. 4.2 and later can be run with projector.

Example:

```bash
$projector config add
Enter a new configuration name: AndroidStudio
Do you want to choose a Projector-installed IDE? [y/n]: n
Enter the path to IDE: /path/to/your/android-studio
...
```

### projector command is unavailable

<a name="no_projector"/>

Default instruction installs `projector` script in directory `~/.local/bin`. If system can't find the script after
installation it means that the directory
`~/.local/bin` was not included in the _PATH_ environment variable. Try the following:

- Restart the terminal. If `projector` was the first executable installed in `~/.local/bin`, and the directory wasn't
  exist when your login session started, it may help.

- In some Linux distributions the directory `~/.local/bin` not included in the `PATH`
  environment variable. In this case add `export  PATH=${PATH}:~/.local/bin` to your `~/.profile`  
  and run `source ~/.profile`.

### WSL issues

WSL is new technology and sometimes there are problems with network interfaces forwarding from Linux to Windows system.
For example: https://github.com/microsoft/WSL/issues/4636 .

If you have issues with accessing Projector running in WSL from browser, try do the following:

- Do not use several WSL machines in the same time. Connectivity issues happens rarely if only one WSL machine is
  running. You can check state of existing WSL machies using `wsl -l -v` command.

- Try command `Get-Service LxssManager | Restart-Service` in PowerShell console

- Restart your WSL environment:
  ```wsl --shutdown```
  and start your linux console again.

*WARNING!* The `wsl --shutdown` command will close all Linux consoles. Save your work before stopping WSL!

- Using docker service with WSL2 backend can cause connectivity issues. Try to disable it and restart WSL terminal.

- Use address other than localhost. Usually WSL have problems forwarding localhost interface only. Try to use listening
  address other than localhost. You can assign HTTP listening address during initial installation or using
  `projector config edit` command.

### projector exits immediately

- Make sure that you installed all packages mentioned in [Prerequisites](#Prerequisites) section.
- Check log-file (it's location shown in console when installer runs the config).
- Make sure that there is no another instance of same config running.

### Using Projector as systemd service

Straightforward creating systemd service to automatically start Projector in the background, lead to projector zombie
process. You can avoid this using projector generated run script instead of using projector run command. For details
refer to the answer of [this](https://youtrack.jetbrains.com/issue/PRJ-298) issue.

