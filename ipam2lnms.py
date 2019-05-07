#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2019 Dag Bakke <igotemail@this.is.a.dummy.com>
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
# of phpipam and librenms. phpipam is considered the master.
# This script will not write to the phpipam db.
#
# The script will not make any changes to librenms unless the '-c' switch is set.
#
# With the '-c' switch set, the script will add hostnames only found in in phpipam,
# to librenms.
#
# Hosts found in librenms are not deleted from librenms unless the '-d' switch is given.
#
# Alternatives to '-d' are '-i(gnore) and -z(zzzzzz - disable)
# The code for ignore/disable is just dummy code for now.
#
# The web ui and the database allows for this, but there is as of yet not a CLI script
# to do it. I do not want to publish a script changing the db directly.
#
# dag - at - bakke - dot - com

from __future__ import print_function
import sys
import argparse
import pymysql as mdb
import subprocess

# To avoid db credentials in the script, I use my.cnf
# Refer to README

############    stuff which may need tuning by you    ################
dbcreds = '~/.my.cnf'

# these denotes stanzas in $dbcreds
librenms = 'librenms'
phpipam = 'phpipam'

# tune these to return only the hosts that matter to you, in column 0.
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

# These are the default SNMP options when adding a host with addhost.php
add_options = 'ap v3' # add '-f' or '-b' as needed. See addhost.php doc.
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
    parser.add_argument("-d", "--deletehosts", action='store_true', default=False,
                        help="hosts not found in phpipam will be deleted from lnms")
    parser.add_argument("-i", "--ignorehosts", action='store_true', default=False,
                        help="hosts not found in phpipam will be marked as ignored in lnms. (dummy for now)")
    parser.add_argument("-z", "--disablehosts", action='store_true', default=False,
                        help="hosts not found in phpipam will be marked as disabled in lnms. (dummy for now)")
    parser.add_argument("-c", "--commit", action='store_true', default=False,
                        help="actually execute commands")
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

    if not myargs.commit: # pretend
        print("This is what will happen if you add the '-c' switch:")
        for host in hosts_unique_to_phpipam:
            print(f"{addcmd} {host} {add_options}")
        for host in hosts_unique_to_librenms:
            if myargs.ignorehosts:
                print(f"{ignorecmd} {host}     <- dummy")
            if myargs.disablehosts:
                print(f"{disablecmd} {host}     <- dummy")
            if myargs.deletehosts:
                print(f"{delcmd} {host}")

    else: # myargs.commit is true
        for host in hosts_unique_to_phpipam:
            add_result = subprocess.run([addcmd, host, add_options], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
            if myargs.verbose:
                print(str(add_result.stdout.decode('UTF-8')).rstrip())

        for host in hosts_unique_to_librenms: # ignore, disable or delete hosts
#            if myargs.ignorehosts:
#                ignore_result = subprocess.run([ignorecmd, host], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
#                if myargs.verbose:
#                    print(str(ignore_result.stdout.decode('UTF-8')).rstrip())

#            if myargs.disablehosts:
#                disable_result = subprocess.run([ignorecmd, host], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
#                if myargs.verbose:
#                    print(str(disable_result.stdout.decode('UTF-8')).rstrip())

            if myargs.deletehosts:
                delete_result = subprocess.run([delcmd, host], check=False, stdout=subprocess.PIPE, shell=False, stderr=subprocess.STDOUT)
                if myargs.verbose:
                    print(str(delete_result.stdout.decode('UTF-8')).rstrip())


if __name__ == '__main__':
    sys.exit(main(sys.argv))
