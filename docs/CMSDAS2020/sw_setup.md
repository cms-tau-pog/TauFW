# 1. Setting up the analysis software

For the entire exercise it is assumed, that you have access to the `lxplus.cern.ch` login nodes at CERN.

To connect to one of these machines (which use CentOS7 as operating system) from a Linux based system at your home institution, please use the following command, which needs to be adapted to your CERN computing account:

```sh
ssh <cern-username>@lxplus.cern.ch
```

You can additionally add on your home machine the following configuration to `~/.ssh/config` to enable for example X11 forwarding and to have a shorter command for connection:

```sh
Host cern7
    Hostname = lxplus.cern.ch
    User = <cern-username>
    Compression = yes
    ForwardX11 = yes
    ForwardAgent = yes
```

After adding this, you can connect to the CERN login nodes simply via `ssh cern7`
