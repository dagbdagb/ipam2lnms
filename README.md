# Synchronizing phpIPAM and LibreNMS

This reason this script (ipam2lnms) exists, is the lack of native support for
phpIPAM in LibreNMS. Combined with the fact that I know just enough python and
SQL to be dangerous, and could not find the motivation to learn enough php and 
LibreNMS to fix said integration myself.

I love both LibreNMS and phpIPAM. But clearly not enough .....

I am hoping for someone with the right combination of php knowledge and 
available time/energy/karmadeficit to create the commands ignorehost.php 
and disablehost.php. Or better yet: make this script obsolete by making 
proper support for phpIPAM in LibreNMS.


Anyways:

The script connects to the LibreNMS and phpIPAM databases, pulls out a 
list of hosts from both, and creates lists of hosts unique to both.
Really, really simple stuff. Less than 200 lines. Read it and verify that 
I am not stealing your family heirloom bashrc.

It then adds hosts unique to phpIPAM, to LibreNMS. Using SNMP credentials from
LibreNMS' config.php.

It can optionally delete hosts from LibreNMS, which are unique to LibreNMS.
I.e. not found in phpIPAM

The script makes no modification to phpIPAM, and only modifies LibreNMS via
the native LibreNMS scripts. The script itself only requires a read-only 
db-account.

There is no config file. A few variables can be set in the script.

The script runs in 'dummy' mode unless you add the '-c' switch.
When adding the '-c' switch, the script is silent save for db connection
errors. This means that hosts whose SNMP credentials are not the same
as in LibreNMS config.php, or hosts which are down or unreachable will
fail silently.

Add '-v' for slightly more verbose output.

I do not currently handle all options of the addhost.php script. In 
particular, hosts must respond to SNMP to be added. 

I will handle the -f, -b and -P switches later.


```
# ./ipam2lnms.py --help
usage: ipam2lnms.py [-h] [-v] [-d] [-i] [-z] [-c]

optional arguments:
  -h, --help          show this help message and exit
  -v, --verbose       show verbose output
  -d, --deletehosts   hosts not found in phpipam will be deleted from lnms
  -i, --ignorehosts   hosts not found in phpipam will be marked as ignored in
                      lnms. (dummy for now)
  -z, --disablehosts  hosts not found in phpipam will be marked as disabled in
                      lnms. (dummy for now)
  -c, --commit        actually execute commands
```


# Database credentials

The script expects you (or the user executing the script) to have a .my.cnf 
with the proper credentials to access the LibreNMS and phpIPAM databases.
The script expects said file to be in $HOME, this can be changed in the script.

```
$ cat .my.cnf
[librenms]
user=librenmsro
password=librenmsro2019
database=librenms
host=localhost

[phpipam]
user=phpipamro
password=phpipamro2019
database=phpipam
host=phpipam
```

If you have a .my.cnf already, do not change what is already there. 
Just add to it. Tune as needed.


To create the db users:
```
phpipamhost$ mysql -u dbadminuser -p
MariaDB [(none)]> grant select on phpipam.* to 'phpipamro'@'10.10.10.101' identified by 'phpipamro2019';
MariaDB [(none)]> flush privileges;
MariaDB [(none)]> \q

librenmshost$ mysql -u dbadminuser -p
MariaDB [(none)]> grant select on librenms.* to 'librenmsro'@'127.0.0.1' identified by 'librenmsro2019';
MariaDB [(none)]> flush privileges;
MariaDB [(none)]> \q
```

The IP address shown in the 'grant' command is the host from which the script
will be executed. I expect most users to run this script on the same host as 
the LibreNMS db. Hence using localhost for accessing that db.

If your phpIPAM db runs on the same host, tune .my.cnf and the grant command
accordingly.





