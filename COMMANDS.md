# projector-installer commands and command line options


# Table of Contents
1. [Help](#Help)
2. [Commands](#Commands)
    1. [IDE commands](#IDE-commands)
    2. [Config commands](#Config-commands)
    3. [Shortcut commands](#Shortcut-commands)
    4. [Install https certificate](#Install-https-certificate)
    5. [Projector defaults](#Projector-defaults)
4. [Configuration options](#Configuration-options)


## Help 

To get help use the following command:
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

## Commands 

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

`projector ide install` or `projector ide install ide_name` - select and install IDE interactively. 
Use `projector install --expert` command to specify all significant projector parameters.  
 
`projector ide autoinstall --config-name name-of-new-config --ide-name name-of-ide [--port port-number] [--hostname hostname] 
[--use-separate-config] [--password rw_password] [--ro-password ro_password]`  - 
install IDE without interaction with user. Parameters --config-name and --ide-name are mandatory. You can find the list of known IDE names using 
(interactive) ide find command. Make sure, that you provided full IDE name, for example:
`projector ide autoinstall --config-name Idea --ide-name "IntelliJ IDEA Ultimate 2020.3.4"` 
The `--use-separate-config` option keeps Idea config, system, plugins and logs 
directories in run config directory and allows running multiple IDE instances.
If no --password and --ro-password options are specified random passwords will be generated.
If only --password option is specified, the value of it will be used as read-only password as well.
User can't specify read-only password only.

`projector ide uninstall` - uninstall IDE interactively 

`projector ide uninstall ide_name` - uninstall the specified IDE 

### Config commands 
`projector config run` - run default or interactively selected configuration with Projector
 
`projector config run configuration` - run the specified configuration

`projector config list` - list all existing configurations
 
`projector config add` - add a new configuration interactively.

`projector config add _config_name_ /path/to/app --port  PORT --hostname=HOST_OR_ADDRESS [--use-separate-config]` - add new config 
without user input. To overwrite existing config use --force flag.
The `--use-separate-config` option keeps Idea config, system, plugins and logs 
directories in run config directory and allows running multiple IDE instances.

`projector config edit` - change an existing configuration

`projector config edit configuration` - change the specified configuration

`projector config remove` - select configuration and remove it 

`projector config remove config_name` - remove the configuration

`projector config remove config_name --uninstall-ide` - remove the configuration and uninstall corresponded IDE if there are 
no other configs, which use this IDE  

`projector config rename from_config_name to_config_name` - rename an existing configuration

`projector config show` - show configuration details

`projector config rebuild` - regenerates all files, related to run config. 
Can be useful after manual run config file edit, or incompatible changes in the installer. 

`projector config update` - updates IDE in a selected config. Please note - 
this command updates IDE installed by projector-installer only. Depending on selected run config 
updates searched in compatible_ide files or on JB release server. 

### Shortcut commands

To simplify usage most useful commands have shortcuts. In simple cases 
(when you have the only IDE installed, or you do not run several IDE instances simultaneously) 
it is enough to use a couple of shortcut commands, such as install and run.

- find  - find available IDE (a shortcut for 'ide find')
 
- install - install IDE interactively (a shortcut for 'ide install')

- autoinstall - install IDE without interaction with user (a shortcut for 'ide autoinstall')

- run - run IDE (a shortcut for 'config run')

### Install https certificate

To make config secure (e.q. use https and wss for connection) use command install-certificate

For autogenerated certificate, use command without parameters:
```
projector install-certificate [config_name] 
```

Certificate for existing domain can be installed with the following command: 

```
projector install-certificate [config_name] --certificate server.cert --key server.key 
```
(config_name is not required)   
Don't forget to configure custom names from installed certificate.
It can be done with 
```
projector config edit config_name 
```
command.

In cases when previous form is not enough the extended command: 
``` 
projector install-certificate [config_name] --certificate server.cert --key server.key --chain chain.pem 
```
allows user to specify the file with certificate chain.

## Projector defaults 
To change projector default hostname the `projector defaults` command can be used.
Try `projector defaults --hostname _name_` or just `projector defaults`.


## Configuration options
Projector installer script has the following configuration options:

--config-directory=path_to_dir - specifies path to configuration directory.

--cache-directory=path_to_dir - specifies path to download cache directory.
