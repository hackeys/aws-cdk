import os.path
from aws_cdk.aws_s3_assets import Asset
import aws_cdk.aws_cloudwatch as cloudwatch
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_cloudtrail as cloudtrail,
    Stack
    #aws_networkfirewall as networkfirewall,
    
)

dirname = os.path.dirname(__file__)
class AwscdkprojStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        #env_name = self.node.try_get_context("env"),
        #amzn_linux = 'ami-0ed9277fb7eb570c9',
        #-----------------------VPC Code --------------------------
        vpc = ec2.Vpc(self, "VPC",
            nat_gateways=0,
            subnet_configuration=[ec2.SubnetConfiguration(name="public",subnet_type=ec2.SubnetType.PUBLIC)]
            )
        #-----------------security group code-------------------------------------
        sec_group = ec2.SecurityGroup(
            self,
            "sec-group-allow-ssh",
            vpc=vpc,
            allow_all_outbound=True,
        )

        # add a new ingress rule to allow port 22 to internal hosts
        
        sec_group.add_ingress_rule(
            peer=ec2.Peer.ipv4('10.0.0.0/16'),
            description="Allow SSH connection", 
            connection=ec2.Port.tcp(22)
        )

        #----------------------firewall Code -----------------------   
        #pub_subnets_id = [subnet.subnet_id for subnet in vpc.public_subnets]
        cfn_firewall = networkfirewall.CfnFirewall(self, "MyCfnFirewall",
            firewall_name="firewallName",
            firewall_policy_arn="firewallPolicyArn",
            subnet_mappings=[networkfirewall.CfnFirewall.SubnetMappingProperty(
            subnet_id= 'subnetId'
            )],
        vpc_id= vpc,

            # the properties below are optional
            delete_protection=False,
            description="description",          
            firewall_policy_change_protection=False,
            subnet_change_protection=False,
            
      #  )
        #---------------------AWS ec2 instance code--------------------
        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")) 
            # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
            ) 
        # Instance
        al2_instance = ec2.Instance(self, "Instance",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=amzn_linux,
             vpc = vpc,
            security_group=sec_group,
             role = role
            )   
        asset_al2 = Asset(self, "userdata-al2", path=os.path.join(dirname, "configure-al2.sh"))
        local_path_al2 = al2_instance.user_data.add_s3_download_command(
                bucket=asset_al2.bucket,
                bucket_key=asset_al2.s3_object_key
            )
        al2_instance.user_data.add_execute_file_command(
                file_path=local_path_al2
        )
        asset_al2.grant_read(al2_instance.role)
        
        dashboard = cloudwatch.Dashboard(self, "MyDashboard",
            dashboard_name="dashboardName",
            end="end",
            period_override=cloudwatch.PeriodOverride.AUTO,
            start="start",
        )       
        trail = cloudtrail.Trail(self, "CloudTrail",
            send_to_cloud_watch_logs=True,
        )