#!/usr/bin/env python
import sys
import re
import boto.ec2
import boto.rds
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


class AwsObject(object):
    def __init__(self, instance):
        self.instance = instance

class RdsObject(AwsObject):
    def name(self, domain):
        return "{}.{}".format(self.instance.id, domain)

    def dns(self):
        return self.instance.endpoint[0]

class Ec2Object(AwsObject):
    def name(self, domain):
        return self.instance.tags["Name"]

    def dns(self):
        return self.instance.public_dns_name

class Aws(object):
    def __init__(self):
        self._ec2 = None
        self._route53 = None
        self._rds = None

    def ec2(self):
        if self._ec2 is None:
            self._ec2 = boto.ec2.connect_to_region(AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        return self._ec2

    def route53(self):
        if self._route53 is None:
            self._route53 = boto.route53.connection.Route53Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        return self._route53

    def rds(self):
        if self._rds is None:
            self._rds = boto.rds.connect_to_region(AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        return self._rds

    def _get_running_rds_intances(self):
        instances = []
        for instance in self.rds().get_all_dbinstances():
            if instance.status == "available":
                instances.append(RdsObject(instance))
        return instances


    def _get_running_ec2_intances(self):
        instances = []
        for reservation in self.ec2().get_all_instances():
            for instance in reservation.instances:
                if instance.state not in ("terminated", "stopped"):
                    instances.append(Ec2Object(instance))
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

    def show_rds(self, instances = None):
        mask = "{:25s} {:10s} {:10s} {:5} {}"
        print mask.format("RDS_ID", "USERNAME", "ENGINE", " PORT", "DNS")
        if instances is None:
            instances = self._get_running_rds_intances()
        for instance in instances:
            instance = instance.instance
            print mask.format(
            instance.id,
            instance.master_username,
            instance.engine,
            instance.endpoint[1],
            instance.endpoint[0],
            )

    def show_ec2(self):
        print "EC2_ID\t\tSTATE\tIP\t\tDNS"
        instances = self._get_running_ec2_intances()
        for instance in instances:
            instance = instance.instance
            print "{}\t{}\t{}\t{:50s}\t{}".format(
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

    def check_parameters(self, domain):
        if domain is None:
            print "As paramenter, please provide DOMAIN_NAME_WHERE_DNS_WILL_BE_SET"
            sys.exit(2)
            return
        if not self.is_valid_dns(domain):
            print "Error: [{}] is not a valid domain.".format(domain)
            sys.exit(1)

    def set_aws_dns(self, domain = None):
        self.check_parameters(domain)
        self.set_rds_dns(domain)
        self.set_ec2_dns(domain)

    def set_rds_dns(self, domain = None):
        self.check_parameters(domain)
        print "Obtaining RDS instances list"
        instances = self._get_running_rds_intances()
        self.show_rds(instances)
        self._set_dns3(domain, instances)

    def set_ec2_dns(self, domain = None):
        self.check_parameters(domain)
        print "Obtaining EC2 instances list which the name looks like a DNS entry"
        instances = self._get_running_ec2_intances()
        instances_to_set_dns = []
        for instance in instances:
            if self.is_interesting_dns(instance.name(domain), domain):
                instances_to_set_dns.append(instance)
                instance = instance.instance
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
                dns_name = "{}.".format(instance.name(domain))
                if record.name == dns_name:
                    deleted_record = records.add_change("DELETE", record.name, record.type, record.ttl)
                    deleted_record.add_value(record.to_print())
                    print deleted_record

        print "Creating new records"
        for instance in instances_to_set_dns:
            new_record = records.add_change("CREATE", instance.name(domain), "CNAME")
            new_record.add_value(instance.dns())
            print "{:50s} CNAME {}".format(instance.name(domain), instance.dns())
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
    valid_args = ("show_dns", "show_ec2", "show_rds", "set_ec2_dns", "set_rds_dns", "set_aws_dns", "show_dns_domains")
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



