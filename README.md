If you use AWS you often have that common problem of launching machines and than feeling the huge pain of configuring a meaningful DNS afterwards.

This scripts solves this issue for good.


a) launch the EC2 machine
b) during the AWS's launch wizard, on the machine name, name it as the DNS entry should be. Example:
    xibrapz.mynicedomain.com

c) aws.py set_ec2_dns mynicedomain.com
d) wait 1 minute because AWS has to sync...
e) ssh ubuntu@xibrapz.mynicedomain.com


Bonus commands:

aws.py show_dns # shows all route53 entries
aws.py show_ec2 # shows all ec2 entries
aws.py show_dns_domains # shows all route53 domains

# how to setup
pip install boto
cp aws_credentials.py.sample aws_credentials.py
emacs aws_credentials.py # add your credentials