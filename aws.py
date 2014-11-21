#!/usr/bin/env python
import sys
import re
import boto.ec2
import boto.route53


from aws_credentials import *

def mdebug(elem):
    print "A--"
    print elem
    print "B--"
    print dir(elem)
    print "C--"
    print elem.__dict__
    print "D--"

class Aws(object):
    def __init__(self):
        self._ec2 = None
        self._route53 = None

    def ec2(self):
        if self._ec2 is None:
            self._ec2 = boto.ec2.connect_to_region(AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        return self._ec2

    def route53(self):
        if self._route53 is None:
            self._route53 = boto.route53.connection.Route53Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        return self._route53

    def _get_running_ec2_intances(self):
        instances = []
        for reservation in self.ec2().get_all_instances():
            for instance in reservation.instances:
                if instance.state not in ("terminated", "stopped"):
                    instances.append(instance)
        return instances

    def show_dns_domains(self):
        zones = self.route53().get_all_hosted_zones().ListHostedZonesResponse.HostedZones
        print "Available domains at route53"
        for zone in zones:
            print zone.Name[:-1]

    def show_dns(self):
        zones = self.route53().get_all_hosted_zones().ListHostedZonesResponse.HostedZones
        for zone in zones:
            print zone.Name
            records = self.route53().get_all_rrsets(zone.Id.split('/')[-1])
            for record in records:
                print "{}\t\t\t{}\t{}\t".format(record.name, record.type, record.to_print())


    def show_ec2(self):
        instances = self._get_running_ec2_intances()
        print "EC2_ID\t\tSTATE\tIP\t\tDNS"
        for instance in instances:
            print "{}\t{}\t{}\t{}\t{}".format(
            instance.id,
            instance.state,
            instance.private_ip_address,
            instance.public_dns_name,
            instance.tags["Name"],
            )

    def _get_recods(self, domain):
        zone = self.route53().get_hosted_zone_by_name("{}.".format(domain))
        records = self.route53().get_all_rrsets(zone.Id.split('/')[-1])
        return records


    def set_ec2_dns(self, domain = None):
        if domain is None:
            print "Usage: set_ec2_dns DOMAIN_NAME_WHERE_DNS_WILL_BE_SET"
            sys.exit(2)
            return
        if not self.is_valid_dns(domain):
            print "Error: [{}] is not a valid domain.".format(domain)
            sys.exit(1)
        print "Obtaining EC2 instances list"
        instances = self._get_running_ec2_intances()
        instances_to_set_dns = []
        for instance in instances:
            if self.is_interesting_dns(instance.tags["Name"], domain):
                instances_to_set_dns.append(instance)
                print "{}\t{}\t{}\t{}\t{}".format(
                instance.id,
                instance.state,
                instance.private_ip_address,
                instance.public_dns_name,
                instance.tags["Name"],
                )


        self._set_dns3(domain, instances_to_set_dns)


    def _set_dns3(self, domain, instances_to_set_dns):
        records = self._get_recods(domain)
        print "Delete existing records..."
        for record in records:
            for instance in instances_to_set_dns:
                dns_name = "{}.".format(instance.tags["Name"])
                if record.name == dns_name:
                    deleted_record = records.add_change("DELETE", record.name, record.type, record.ttl)
                    deleted_record.add_value(record.to_print())
                    print deleted_record

        print "Creating new records"
        for instance in instances_to_set_dns:
            name = instance.tags["Name"]
            new_record = records.add_change("CREATE", name, "CNAME", 60)
            new_record.add_value(instance.public_dns_name)
            print "CNAME: {}, {}".format(name, instance.public_dns_name)
        print "Saving..."
        print records.commit()
        print "Done"

    def is_valid_dns(self, name):
        rgx = re.compile("^[a-z0-9-]+\\.([a-z0-9-]+\\.)*[a-z0-9-]+$")
        return rgx.search(name) != None

    def is_interesting_dns(self, name, domain):
        domain = domain.replace(".", "\.")
        rgx = re.compile("^([a-z0-9-]+\.)+{}$".format(domain))
        return rgx.search(name) != None



def main():
    valid_args = ("show_dns", "show_ec2", "set_ec2_dns", "show_dns_domains")
    if len(sys.argv) == 1 or sys.argv[1] not in valid_args:
        print "valid_args: {}".format(valid_args)
        return
    command = sys.argv[1]
    parameters = sys.argv[2:]

    result = getattr(Aws(), command)(*parameters)
    if result != None:
        print result

if __name__ == "__main__":
    main()



