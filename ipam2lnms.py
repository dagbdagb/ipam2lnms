#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2019 Dag Bakke <igotemail@thisisadummy.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
# This script compares the hostnames found in the devices tables
# of phpIPAM and LibreNMS. phpIPAM is considered the master.
#
# This script will not write to the phpIPAM db, and may change the
# LibreNMS only if the '-c' switch is set.
#
#
# See README.md for further information.
#
# dag - at - bakke - dot - com

import sys
import argparse
import pymysql as mdb
import subprocess


############    stuff which may need tuning by you    ################
dbcreds = '~/.my.cnf' # See README.md

# these denotes stanzas in $dbcreds
librenms = 'librenms'
phpipam = 'phpipam'

# tune these two to return only the hosts that matter to you, in column 0.
sql_query_librenms = '''
SELECT hostname
FROM devices
WHERE hostname LIKE "%-fw"
'''

sql_query_phpipam = '''
SELECT hostname
FROM devices
WHERE hostname LIKE "%-fw"
'''

add_options = 'ap v3' # default SNMP options
#############       end         ###################

addcmd = '/opt/librenms/addhost.php'
delcmd = '/opt/librenms/delhost.php'
ignorecmd = '/opt/librenms/ignorehost.php' # I would like this command to exist
disablecmd = '/opt/librenms/disablehost.php' # This too.


def getdbdata(query, db, verbose):
    mylist = []

    try:
        con = mdb.connect(read_default_file=dbcreds, read_default_group=db)
        cursor = con.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            mylist.append(row[0])

        if verbose:
            if len(mylist) == 0:
                print(f"{db}\t: query returns no data")
            if len(mylist) > 0:
                print(f"{db}\t: ok")

    except Exception as ex:
        print(f"{db}\t: got an exception" + str(ex))

    finally:
        if con:
            con.close()

    return mylist


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true', default=False,
                        help="show verbose output")
    parser.add_argument("-a", "--addhosts", action='store_true', default=False,
                        help="hosts only found in phpipam will be added to lnms")
    parser.add_argument("-d", "--deletehosts", action='store_true', default=False,
                        help="hosts not found in phpipam will be deleted from lnms")
    parser.add_argument("-i", "--ignorehosts", action='store_true', default=False,
                        help="hosts not found in phpipam will be marked as ignored in lnms. (dummy for now)")
    parser.add_argument("-z", "--disablehosts", action='store_true', default=False,
                        help="hosts not found in phpipam will be marked as disabled in lnms. (dummy for now)")
    parser.add_argument("-c", "--commit", action='store_true', default=False,
                        help="actually execute commands")
    parser.add_argument("-f", "--force", action='store_true', default=False,
                        help="forces the device to be added by skipping the icmp and snmp check against the host.")
    parser.add_argument("-b", action='store_true', default=False,
                        help="Add the host with SNMP if it replies to it, otherwise only ICMP.")
    parser.add_argument("-P", action='store_true', default=False,
                        help="Add the host with only ICMP, no SNMP or OS discovery.")
    myargs = parser.parse_args()

    hosts_unique_to_librenms = []
    hosts_unique_to_phpipam = []

    hosts_in_librenms = getdbdata(sql_query_librenms, librenms, myargs.verbose)
    hosts_in_phpipam = getdbdata(sql_query_phpipam, phpipam, myargs.verbose)

    for host in hosts_in_librenms:
        if host not in hosts_in_phpipam:
            hosts_unique_to_librenms.append(host)

    for host in hosts_in_phpipam:
        if host not in hosts_in_librenms:
            hosts_unique_to_phpipam.append(host)

    if myargs.verbose:
        print("\nhosts unique to librenms:\n" + str(hosts_unique_to_librenms))
        print("\nhosts unique to phpipam:\n" + str(hosts_unique_to_phpipam) + "\n")

    forceopts = ""
    if myargs.force:
        forceopts += "f"
    if myargs.b:
        forceopts += "b"
    if myargs.P:
        forceopts += "P"
    if forceopts:
        forceopts = "-" + forceopts

    if not myargs.commit: # pretend
        print("This is what will happen if you add the '-c' switch:")
        for host in hosts_unique_to_phpipam:
            if myargs.addhosts:
                print(f"{addcmd} {forceopts} {host} {add_options}")
        for host in hosts_unique_to_librenms:
            if myargs.ignorehosts:
                print(f"{ignorecmd} {host}     <- dummy")
            if myargs.disablehosts:
                print(f"{disablecmd} {host}     <- dummy")
            if myargs.deletehosts:
                print(f"{delcmd} {host}")

    else: # myargs.commit is true
        for host in hosts_unique_to_phpipam:
            if myargs.addhosts:
                add_result = subprocess.run([addcmd, forceopts, host, add_options], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
                if myargs.verbose:
                    print(str(add_result.stdout.decode('UTF-8')).rstrip())

        for host in hosts_unique_to_librenms: # ignore, disable or delete hosts
#            if myargs.ignorehosts:
#                ignore_result = subprocess.run([ignorecmd, host], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
#                if myargs.verbose:
#                    print(str(ignore_result.stdout.decode('UTF-8')).rstrip())

#            if myargs.disablehosts:
#                disable_result = subprocess.run([disablecmd, host], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
#                if myargs.verbose:
#                    print(str(disable_result.stdout.decode('UTF-8')).rstrip())

            if myargs.deletehosts:
                delete_result = subprocess.run([delcmd, host], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
                if myargs.verbose:
                    print(str(delete_result.stdout.decode('UTF-8')).rstrip())


if __name__ == '__main__':
    sys.exit(main(sys.argv))
