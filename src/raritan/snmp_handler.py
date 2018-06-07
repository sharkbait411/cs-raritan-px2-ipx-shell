import os
import cloudshell.api.cloudshell_api as cs_api

from cloudshell.shell.core.context_utils import get_attribute_by_name
from cloudshell.snmp.quali_snmp import QualiSnmp
from cloudshell.snmp.snmp_parameters import SNMPParameters, SNMPV2ReadParameters, SNMPV2WriteParameters, SNMPV3Parameters
from pysnmp.smi.rfc1902 import ObjectType
from log_helper import LogHelper


class SnmpHandler:
    def __init__(self, context):

        self.session = cs_api.CloudShellAPISession(host=context.connectivity.server_address,
                                                   token_id=context.connectivity.admin_auth_token,
                                                   domain="Global")
        self.context = context
        self.logger = LogHelper.get_logger(context)

        self.address = self.context.resource.address

        self.community_read = self.session.DecryptPassword(get_attribute_by_name(context=self.context,
             attribute_name='SNMP Read Community')).Value or 'public'

        self.community_write = self.session.DecryptPassword(get_attribute_by_name(context=self.context,
            attribute_name='SNMP Write Community')).Value or 'private'
        self.port = int(get_attribute_by_name(context=self.context, attribute_name='SNMP Port')) or 161,
        self.password = get_attribute_by_name(context=self.context, attribute_name='SNMP Password') or '',
        self.user = get_attribute_by_name(context=self.context, attribute_name='SNMP User') or '',
        self.version = get_attribute_by_name(context=self.context, attribute_name='SNMP Version')
        self.private_key = get_attribute_by_name(context=self.context, attribute_name='SNMP Private Key')

    def get(self, object_identity):
        handler = self._get_handler('get')

        return handler.get(ObjectType(object_identity))

    def set(self, object_identity, value):
        handler = self._get_handler('set')

        return handler._command(handler.cmd_gen.setCmd, ObjectType(object_identity, value))

    def get_raw_handler(self, action):
        return self._get_handler(action)

    def _get_handler(self, action):
        mib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mibs'))
        snmp_parameters = self._get_snmp_parameters(action)

        handler = QualiSnmp(snmp_parameters, self.logger)
        handler.update_mib_sources(mib_path)
        handler.load_mib(['PDU2-MIB'])

        return handler

    def _get_snmp_parameters(self, action):
        if '3' in self.version:
            return SNMPV3Parameters(ip=self.address,
                                    snmp_user=self.user,
                                    snmp_password=self.password,
                                    snmp_private_key=self.private_key)
        else:
            if action.lower() == 'set':
                community = self.community_write
            else:
                community = self.community_read

            return SNMPV2ReadParameters(ip=self.address,
                                        snmp_read_community=community)
