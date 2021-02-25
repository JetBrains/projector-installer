# projector-installer changelog

Notable changes to this project are documented in this file.

# 0.1.19

## Fixed

- missed carriage return on default selection in Linux Mint

## Added

- projector config update command for IDE update

## Changed

- Projector server v0.51.15

# 0.1.18

**Important note**: Starting from this version users can use install-certificate command to make run config secure. Read
more [here](./COMMANDS.md#Install-https-certificate)

## Added

- install-certificate command without provided certificate autogenerates certificate
- --expert option for install and config add commands

## Changed

- User is not asked on port number during install and config add. Change default port using config edit if you wish.
- Fresh installed IDE autoruns by default. Behaviour can be changed via --no-auto-run option
- User is not asked for secure config creation during install and config add commands
- install and config add commands asks only for IDE by default. To change behaviour use --expert option.

# 0.1.17

## Added

- User certificate support (see new install-certificate command)

# 0.1.16

## Changed

- Projector server v0.50.14
- user-specified DNS-names added to standard configuration process
- Only custom names used in access URLs if specified.
- TAB completion works when user enters path to IDE
- _config edit_ command allows change all run config parameters

# 0.1.15

## Added

- Support for user-specified DNS names during certificate generation
- Support finding and installing not tested IDEs (using IDE list from JB release server)

# 0.1.14

## Added

- Support IDEs installed and managed via JetBrains Toolbox

# 0.1.13

## Added

- Logging for keytool errors

# 0.1.12

## Changed

- Reworked documentation
- Projector server v0.49.13

# 0.1.11

**Important note**: starting with this version, there is no more custom Markdown plugin required to support Markdown
rendering. If you used projector-installer before this version, please manually remove custom Projector Markdown plugin
from the IDE and enable bundled Markdown plugin.

## Added

- add fqdn of host to SAN certificates
- output Projector server stdout to console on error
- check for new projector-installer version on startup

## Fixed

- browser autorun in WSL

## Changed

- lazy init of compatible app list
- Projector server v0.48.12
- projector log is run_config specific now

## Removed

- projector config update-markdown-plugin command

# 0.1.10

## Added

- new config subcommand - rebuild
- Projector server v0.47.11
- switched to client version bundled in server

# 0.1.9

## Added

- Projector server v0.46.10
- New command line option --cache-directory
- Android Studio 4.2 Canary 12 compatibility
- JVM version check
- http server can listen on all local addresses (0.0.0.0 or *)
- password protected connection support
