# A tool to set AWS's route53 DNS according to EC2 names

If you use AWS you often have that common problem of launching machines and than feeling the huge pain of configuring a meaningful DNS afterwards.

This scripts solves this issue for good.


1. launch the EC2 machine

1. during the AWS's launch wizard, on the machine name, name it as the DNS entry should be. Example:
    xibrapz.mynicedomain.com

1. aws.py set_ec2_dns mynicedomain.com

1. wait 1 minute because AWS has to sync

1. ssh ubuntu@xibrapz.mynicedomain.com


# Bonus commands:

```
aws.py show_dns # shows all route53 entries
aws.py show_ec2 # shows all ec2 entries
aws.py show_dns_domains # shows all route53 domains
```

# How to setup:
```
pip install boto
cp aws_credentials.py.sample aws_credentials.py
emacs aws_credentials.py # add your credentials
```
