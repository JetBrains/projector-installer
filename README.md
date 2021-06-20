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
    8. [Change existing configuration](#Change-existing-configuration)
    9. [FreeBSD support](#FreeBSD-support)
   10. [OpenBSD support](#OpenBSD-support)
   11. [projector config update does not work](#config-update-does-not-work)
    
### <a id="Change-existing-configuration"></a>

## Installation<a id="Installation"></a>

### Prerequisites

To use projector-installer you need machine with Linux (or WSL) and with Python 3.6 or higher. Before install
projector-installer make sure that: 

1. python3, pip3 and python3-crypto are installed in your system. 
   In Debian-based distributions you can install them using the command:
    ```bash
    sudo apt install python3 python3-pip -y
    sudo apt install python3-cryptography -y
    ```
    
    In CentOS use commands:
    ```bash
    # CentOS 8+
    sudo dnf install python3 python3-pip python3-pyOpenSSL python3-cryptography -y
    # CentOS 7 / Amazon Linux 2
    sudo yum install python3 python3-pip pyOpenSSL python-cryptography -y
    ```

2. Update pip. 

    For Debian-based distributions run 
    ```bash
    python3 -m pip install -U pip 
    ```

    For CentOS use command: 
    ```bash
    python3 -m pip install -U pip --user 
    ```

3. Make sure that you have installed the following packages:
- less 
- libxext6
- libxi6
- libxrender1
- libxtst6
- libfreetype6

    For Debian-based distributions you can install them using the command:

    ```bash
    sudo apt install less libxext6 libxrender1 libxtst6 libfreetype6 libxi6 -y  
    ```    
  
    For CentOS use command:
    ```bash
    sudo yum install less libXext libXrender libXtst libXi freetype -y  
    ```

### Install from PyPi

You can install projector-installer script from PyPi, using command:

```bash
pip3 install projector-installer --user
```
`projector` script will be installed in `~/.local/bin` directory. To make it available 
on Debian-based systems run: 
```bash
source ~/.profile 
```
for CentOS run: 
```bash 
source ~/.bash_profile
``` 

The command `projector` should be available now.

_NOTE:_ If it is not so, please refer to the [appropriate section](#projector-command-is-unavailable) in the [FAQ](#FAQ).

_NOTE:_ projector script checks for updates on start. If a new version is available, you can install an update using
command
`pip3 install projector-installer --upgrade --user`

## Quick start<a id="Quick-start"></a>

The first time you run projector, it will automatically download, install, configure and start IDE. Just run projector and
follow the instructions. The script will run the installed IDE with projector-server and display URLs to access it. Open
a URL in your browser and use IDE as usual.

To run IDE again use `projector run`

To install a new IDE run `projector install`

To find out which JetBrains IDEs are supported, run `projector find`

To get help projector commands run `projector --help`

If you want to know more on projector usage please refer to
[this](https://github.com/JetBrains/projector-installer/blob/master/COMMANDS.md) file.

## FAQ<a id="FAQ"></a>

### Secure connection<a id="Secure-connection"></a>

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

### projector-installer config directory<a id="projector-installer-config-directory"></a>

projector-installer keeps downloaded IDE and run configurations in the configuration directory. Usually configuration
directory is ~/.projector. User can specify another location for it, using option --config-directory, for example:
`projector --config-directory=config run`

### Android Studio support<a id="Android-Studio-support"></a>

Projector installer can't support automatic Android Studio installation due to legal issues. However, installer can help
you to configure already installed Android Studio to use with Projector. To make new run config for Android Studio
use the `projector config add`
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

### projector command is unavailable<a id="projector-command-is-unavailable"></a>

Default instruction installs `projector` script in directory `~/.local/bin`. If system can't find the script after
installation it means that the directory `~/.local/bin` was not included in the _PATH_ environment variable. 
Try the following:

- Restart the terminal. If `projector` was the first executable installed in `~/.local/bin`, and the directory wasn't
  exist when your login session started, it may help.

- In some Linux distributions the directory `~/.local/bin` not included in the `PATH`
  environment variable. In this case add `export  PATH=${PATH}:~/.local/bin` to your `~/.profile`  
  and run `source ~/.profile`.

### WSL issues<a id="WSL-issues"></a>

WSL is new technology and sometimes there are problems with network interfaces forwarding from Linux to Windows system.
For example: https://github.com/microsoft/WSL/issues/4636 .

If you have issues with accessing Projector running in WSL from the browser, try the following:

- Do not use several WSL machines in the same time. Connectivity issues rarely happens if only one WSL machine is
  running. You can check state of existing WSL machines using `wsl -l -v` command.

- Try command `Get-Service LxssManager | Restart-Service` in PowerShell console

- Restart your WSL environment:
  ```wsl --shutdown```
  and start your linux console again.

*WARNING!* The `wsl --shutdown` command will close all Linux consoles. Save your work before stopping WSL!

- Using docker service with WSL2 backend can cause connectivity issues. Try to disable it and restart WSL terminal.

- Use address other than localhost. Usually WSL have problems forwarding localhost interface only. Try to use listening
  address other than localhost. You can assign HTTP listening address during initial installation or using
  `projector config edit` command.

### projector exits immediately<a id="projector-exits-immediately"></a>

- Make sure that you installed all packages mentioned in [Prerequisites](#Prerequisites) section.
- Check log-file (it's location shown in console when installer runs the config).
- Make sure that there is no another instance of same config running.

### Using Projector as systemd service<a id="Using-Projector-as-systemd-service"></a>

Straightforward creating systemd service to automatically start Projector in the background, lead to projector zombie
process. You can avoid this using projector generated run script instead of using projector run command. For details
refer to the answer of [this](https://youtrack.jetbrains.com/issue/PRJ-298) issue.

### Change existing configuration<a id="Change-existing-configuration"></a>
To change run config (for example - change listening port or access password) use command 
```commandline
projector config edit
```

### projector config update does not work<a id="config-update-does-not-work"></a>
Probably your run configuration uses "tested" update channel.
Try change update channel to not_tested.
You can inspect view update channel using `projector config show` command and
change it via `projector config edit`.

### FreeBSD support<a id="FreeBSD-support"></a>
projector-installer since ver. 1.1.0 has FreeBSD support.
To run Projector on FreeBSD perform the following steps
(tested on FreeBSD-RELEASE 12.2):


- install python 3.7 with necessary packages:
```commandline
sudo pkg install python37
sudo pkg install py37-pip
sudo pkg install py37-cryptography 
```

- install openjdk11:
```commandline
sudo pkg install openjdk11
```
Do not forget add to fstab fdeskfs and procfs:
```commandline
fdesk /dev/fd fdeskfs rw  0 0
proc  /proc   procfs  rw  0 0
```
and mount them:
```commandline
mount -a
```

- install projector-installer from sources as described [here](https://github.com/JetBrains/projector-installer/blob/master/README-DEV.md#Install-from-source)

pip may fire several warning messages on incompatible cryptography module. 
   You can safely ignore them.

- add ~/.local/bin directory to PATH variable.

- run `projector` as usual 

### OpenBSD support<a id="OpenBSD-support"></a>
projector-installer since ver. 1.1.0 has OpenBSD support.
To run Projector on OpenBSD perform the following steps
(tested on OpenBSD 6.8):

- it is expected, that filesets xbase, xfont, xserv and xshare
are already installed in your system. If it is not so add them as described here:
  https://www.openbsd.org/faq/faq4.html#FilesNeeded
  
- install python 3.7 or later:
```commandline
doas pkg_add python
```

- install pip:
```commandline
doas pkg_add py3-pip    
```
Do not forget to make the symbolic link for installed pip to  /usr/local/bin/pip.

- install py3-cryptography:
```commandline
doas pkg_add py3-cryptography
```

- install openjdk11 
```commandline
doas pkg_add jdk
```
Do not forget to define JAVA_HOME variable and add $JAVA_HOME/bin to PATH variable.  

- install projector-installer from sources as described [here](https://github.com/JetBrains/projector-installer/blob/master/README-DEV.md#Install-from-source)
or install from pypi using 
```commandline
pip install projector-installer
```  
 
- add ~/.local/bin directory to PATH variable.

- run `projector` as usual 
