from src.raritan.snmp_handler import SnmpHandler
from cloudshell.shell.core.context import AutoLoadResource, AutoLoadDetails, AutoLoadAttribute
from src.raritan.log_helper import LogHelper


class RaPxPduAutoloader(object):
    def __init__(self, context):
        self.context = context
        self.logger = LogHelper.get_logger(self.context)
        self.snmp_handler = SnmpHandler(self.context).get_raw_handler('get')

    def autoload(self):
        rv = AutoLoadDetails()
        rv.resources = []
        rv.attributes = []

        rv.attributes.append(self.makeattr('', 'Location', self.snmp_handler.get_property('PDU2-MIB', 'sysLocation', 0)))
        rv.attributes.append(self.makeattr('', 'Model', self.snmp_handler.get_property('PDU2-MIB', 'sysDescr', 0)))
        rv.attributes.append(self.makeattr('', 'Serial Number', self.snmp_handler.get_property('PDU2-MIB', 'pduSerialNumber', 0)))
        rv.attributes.append(self.makeattr('', 'Vendor', self.snmp_handler.get_property('PDU2-MIB', 'pduManufacturer', 0)))
        rv.attributes.append(self.makeattr('', 'Version', self.snmp_handler.get_property('PDU2-MIB', 'boardFirmwareVersion', 0)))

        pdu_name = self.snmp_handler.get_property('PDU2-MIB', 'sysName', 0)

        outlet_table = self.snmp_handler.get_table('PDU2-MIB', 'pmPowerMgmtOutletsTable')
        for index, attribute in outlet_table.iteritems():
            name = 'Outlet %s' % index
            relative_address = index
            unique_identifier = '%s.%s' % (pdu_name, index)

            rv.resources.append(self.makeres(name, 'Generic Power Socket', relative_address, unique_identifier))
            rv.attributes.append(self.makeattr(relative_address, 'Port Description', attribute['pmPowerMgmtOutletsTablePortName']))

        return rv

    def makeattr(self, relative_address, attribute_name, attribute_value):
        a = AutoLoadAttribute()
        a.relative_address = relative_address
        a.attribute_name = attribute_name
        a.attribute_value = attribute_value
        return a

    def makeres(self, name, model, relative_address, unique_identifier):
        r = AutoLoadResource()
        r.name = name
        r.model = model
        r.relative_address = relative_address
        r.unique_identifier = unique_identifier
        return r


class PmPduHandler:
    class Port:
        def __init__(self, port):
            self.address, port_details = port.split('/')
            self.port_number, self.pdu_number, self.outlet_number = port_details.split('.')

    def __init__(self, context):
        self.context = context
        self.logger = LogHelper.get_logger(self.context)
        self.snmp_handler = SnmpHandler(self.context)

    def get_inventory(self):
        autoloader = PmPduAutoloader(self.context)

        return autoloader.autoload()

    def power_cycle(self, port_list, delay):
        self.logger.info("Power cycle called for ports %s" % port_list)
        for raw_port in port_list:
            self.logger.info("Power cycling port %s" % raw_port)
            port = self.Port(raw_port)
            self.logger.info("Powering off port %s" % raw_port)
            self.snmp_handler.set(ObjectIdentity('PM-MIB', 'pmPowerMgmtOutletsTablePowerControl', port.port_number, port.pdu_number, port.outlet_number),
                                  Gauge32(3))
            self.logger.info("Sleeping %f second(s)" % delay)
            sleep(delay)
            self.logger.info("Powering on port %s" % raw_port)
            self.snmp_handler.set(ObjectIdentity('PM-MIB', 'pmPowerMgmtOutletsTablePowerControl', port.port_number, port.pdu_number, port.outlet_number),
                                  Gauge32(2))

    def power_off(self, port_list):
        self.logger.info("Power off called for ports %s" % port_list)
        for raw_port in port_list:
            self.logger.info("Powering off port %s" % raw_port)
            port = self.Port(raw_port)
            self.snmp_handler.set(ObjectIdentity('PM-MIB', 'pmPowerMgmtOutletsTablePowerControl', port.port_number, port.pdu_number, port.outlet_number),
                                  Gauge32(3))

    def power_on(self, port_list):
        self.logger.info("Power on called for ports %s" % port_list)
        for raw_port in port_list:
            self.logger.info("Powering on port %s" % raw_port)
            port = self.Port(raw_port)
            self.snmp_handler.set(ObjectIdentity('PM-MIB', 'pmPowerMgmtOutletsTablePowerControl', port.port_number, port.pdu_number, port.outlet_number),
                                  Gauge32(2))

