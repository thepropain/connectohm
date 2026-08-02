###### The symlinks list. It's not set in stone which way (or even IF) we do the links yet, but at least while I'm working on the project, keeping the files local and the links to them remote makes my life easier.

- 99-connectohm.rules -> /etc/udev/rules/99-connectohm.rules

- ctohm-menu.py -> /usr/local/bin/ctohm-menu.py

- ctohm-menu.service -> /etc/systemd/system/ctohm-menu.service

- ctohm-ppp -> /etc/ppp/peers/ctohm-ppp

- ctohm-settings.sh -> /usr/local/bin/ctohm-settings.sh

- oledfont.pbm -> /usr/local/lib/oledfont.pbm

- oledfont.pil -> /usr/local/lib/oledfont.pil

- rules.v4 -> /etc/iptables/rules.v4

- pap-secrets -> /etc/ppp/pap-secrets

- ctohm-halt<sup>1</sup> -> /lib/systemd/system-shutdown/ctohm-halt

- ctohm-boot<sup>2</sup> -> /usr/local/bin/ctohm-boot

<sup>1</sup> obtained from compiling ctohm-halt.c (`gcc -O2 ctohm-halt.c -o ctohm-halt`)

<sup>2</sup> obtained from compiling ctohm-halt.c (`gcc -O2 ctohm-boot.c -o ctohm-boot`)
