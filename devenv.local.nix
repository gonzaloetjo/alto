# Local config for ALTO development
{ pkgs, ... }:
{
  alto.enable = true;
  alto.devMode = true;  # Only deploy alto-dev agent + skill, skip consumer stuff
}
