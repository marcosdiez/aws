# A tool to set AWS's route53 DNS CNAME entries according to EC2/RDS names

If you use AWS you often have that common problem of launching machines and than feeling the huge pain of configuring a meaningful DNS afterwards.

This scripts solves this issue for good.


1. launch as many EC2/RDS machines as you want

1. during the AWS's launch wizard, on the machine name, name it as the DNS entry should be.
* if it is an EC2 machine, name it as the whole DNS CNAME entry: xibrapz.mynicedomain.com
* if it is a  RDS machine, name it the beginning of the DNS entry: mydb04

1. aws.py set_aws_dns mynicedomain.com

1. wait 10 seconds because AWS has to sync

1. ssh ubuntu@xibrapz.mynicedomain.com
1. mysql -u superuser -u mydb04.mynicedomain.com


# Bonus commands:

```
aws.py show_dns # shows all route53 entries
aws.py show_ec2 # shows all ec2 entries
aws.py show_rds # shows all rds entries
aws.py show_dns_domains # shows all route53 domains

aws.py set_ec2_dns DOMAIN # same as set_aws_dns, EC2 only
aws.py set_rds_dns DOMAIN # same as set_aws_dns, RDS only

```
# How to setup:
```
pip install boto
cp aws_credentials.py.sample aws_credentials.py
emacs aws_credentials.py # add your credentials
```
