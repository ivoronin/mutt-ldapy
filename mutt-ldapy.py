#!/usr/bin/env python
from __future__ import print_function
import sys
from os.path import expanduser
import ConfigParser
import ldap


class MuttLDAPy(object):
    CONFIG_FILE = '~/.mutt-ldapy.conf'
    CONFIG_SECTION = 'mutt-ldapy'
    CONFIG_DEFAULTS = {
        'binddn': None, 'password': None, 'basedn': '',
        'mail_attr': 'mail', 'name_attr': 'cn',
        'filter': '(&(|(%(name_attr)s=*%%(query)s*)'
                  '(%(mail_attr)s=*%%(query)s*))'
                  '(objectclass=person))',
    }
    CONFIG_OPTIONS = CONFIG_DEFAULTS.keys() + ['uri']

    def __init__(self):
        try:
            config = ConfigParser.SafeConfigParser(self.CONFIG_DEFAULTS)
            config.readfp(open(expanduser(self.CONFIG_FILE), 'r'))
            self._options = {option: config.get(self.CONFIG_SECTION, option)
                             for option in self.CONFIG_OPTIONS}
        except (ConfigParser.Error, IOError) as exc:
            sys.exit('Error reading %s: %s' % (self.CONFIG_FILE, exc))

        try:
            self._ldap = ldap.initialize(self._options['uri'])
            if self._options['binddn'] and self._options['password']:
                self._ldap.bind(self._options['binddn'],
                                self._options['password'])
        except ldap.LDAPError as exc:
            sys.exit('Error connecting to %s: %s' % (self._options['uri'], exc))

    def query(self, query):
        results = []
        try:
            for (dname, attrs) in self._ldap.search_s(
                    self._options['basedn'], ldap.SCOPE_SUBTREE,
                    self._options['filter'] % {'query': query}):
                try:
                    results.append([attrs[self._options[option]][0]
                                  for option in 'mail_attr', 'name_attr'])
                except KeyError as exc:
                    sys.exit('Found an object %s without an attribute %s' % (dname, exc))
        except ldap.LDAPError as exc:
            sys.exit('Error querying %s: %s' % (self._options['uri'], exc))

        if results:
            print('EMAIL\tNAME')
            map(lambda (m,n): print('%s\t%s' % (m,n)), results)

if __name__ == '__main__':
    if len(sys.argv) < 2 or not sys.argv[1]:
        sys.exit('Usage: mutt-ldapy <query>')
    MuttLDAPy().query(sys.argv[1])
