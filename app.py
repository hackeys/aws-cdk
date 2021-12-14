#!/usr/bin/env python3

import aws_cdk as cdk

from awscdkproj.awscdkproj_stack import AwscdkprojStack


app = cdk.App()
AwscdkprojStack(app, "awscdkproj")

app.synth()
