# projector-installer commands and command line options


# Table of Contents
1. [Help](#Help)
2. [Commands](#Commands)
    1. [IDE commands](#IDE commands)
    2. [Config commands](#Config commands)
    3. [Shortcut commands](#Shortcut commands)
4. [Configuration options](#Configuration options)


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

### Shortcut commands

To simplify usage most useful commands have shortcuts. In simple cases 
(when you have the only IDE installed, or you do not run several IDE instances simultaneously) 
it is enough to use a couple of shortcut commands, such as install and run.

- find  - find available IDEs (a shortcut for 'ide find')
 
- install - install IDE (a shortcut for 'ide install')

- run - run IDE (a shortcut for 'config run')

## Configuration options
Projector installer script has the following configuration options:

--config-directory=path_to_dir - specifies path to configuration directory.

--cache-directory=path_to_dir - specifies path to download cache directory.
