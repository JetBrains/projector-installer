# projector-installer changelog

Notable changes to this project are documented in this file.

# Unreleased
## Added 
 - add fqdn of host to SAN certificates
 - output Projector server stdout to console on error

## Fixed
 - browser autorun in WSL 
 
## Changed
 - lazy init of compatible app list
 - Projector server v0.48.12
 
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
