#!/bin/bash

read -p "Enter the name of the aws key pair " key_pair_name

key_pair_id=`aws ec2 describe-key-pairs --filters Name=key-name,Values=$key_pair_name --query KeyPairs[*].KeyPairId --output text`

echo $key_pair_id

aws ssm get-parameter --name /ec2/keypair/$key_pair_id --with-decryption --query Parameter.Value --output text > $key_pair_name.pem
