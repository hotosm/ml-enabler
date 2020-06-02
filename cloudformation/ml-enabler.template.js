const cf = require('@mapbox/cloudfriend');
const batch = require('./batch');

const Parameters = {
    GitSha: {
        Type: 'String',
        Description: 'GitSha to Deploy'
    },
    ContainerCpu: {
        Description: 'How much CPU to give to the container. 1024 is 1 cpu. See aws docs for acceptable cpu/mem combinations',
        Default: 1024,
        Type: 'Number'
    },
    ContainerMemory: {
        Description: 'How much memory in megabytes to give to the container. See aws docs for acceptable cpu/mem combinations',
        Default: 1024,
        Type: 'Number'
    },
    SSLCertificateIdentifier: {
        Type: 'String',
        Description: 'SSL certificate for HTTPS protocol'
    },
    DatabaseType: {
        Type: 'String',
        Default: 'db.t3.micro',
        Description: 'Database size to create',
        AllowedValues: [
            'db.t3.micro',
            'db.m4.xlarge'
        ]
    },
    DatabaseUser: {
        Type: 'String',
        Description: 'Database Username'
    },
    DatabasePassword: {
        Type: 'String',
        Description: 'Database User Password'
    },
    MapboxAccessToken: {
        Type: 'String',
        Description: 'Mapbox API Token'
    }
};

const Resources = {
    MLEnablerLogs: {
        Type: 'AWS::Logs::LogGroup',
        Properties: {
            LogGroupName: cf.stackName,
            RetentionInDays: 7
        }
    },
    MLEnablerVPC: {
        Type: 'AWS::EC2::VPC',
        Properties: {
            EnableDnsHostnames: true,
            EnableDnsSupport: true,
            CidrBlock: '172.31.0.0/16',
            Tags: [{
                Key: 'Name',
                Value: cf.join('-', [cf.stackName, 'vpc'])
            }]
        }
    },
    MLEnablerSubA: {
        Type: 'AWS::EC2::Subnet',
        Properties: {
            AvailabilityZone: cf.findInMap('AWSRegion2AZ', cf.region, '1'),
            VpcId: cf.ref('MLEnablerVPC'),
            CidrBlock: '172.31.1.0/24',
            MapPublicIpOnLaunch: true
        }
    },
    MLEnablerSubB: {
        Type: 'AWS::EC2::Subnet',
        Properties: {
            AvailabilityZone: cf.findInMap('AWSRegion2AZ', cf.region, '2'),
            VpcId: cf.ref('MLEnablerVPC'),
            CidrBlock: '172.31.2.0/24',
            MapPublicIpOnLaunch: true
        }
    },
    MLEnablerInternetGateway: {
        Type: 'AWS::EC2::InternetGateway',
        Properties: {
            Tags: [{
                Key: 'Name',
                Value: cf.join('-', [cf.stackName, 'gateway'])
            },{
                Key: 'Network',
                Value: 'Public'
            }]
        }
    },
    MLEnablerVPCIG: {
        Type: 'AWS::EC2::VPCGatewayAttachment',
        Properties: {
            InternetGatewayId: cf.ref('MLEnablerInternetGateway'),
            VpcId: cf.ref('MLEnablerVPC')
        }
    },
    MLEnablerRouteTable: {
        Type: 'AWS::EC2::RouteTable',
        Properties: {
            VpcId: cf.ref('MLEnablerVPC'),
            Tags: [{
                Key: 'Network',
                Value: 'Public'
            }]
        }
    },
    PublicRoute: {
        Type: 'AWS::EC2::Route',
        DependsOn:  'MLEnablerVPCIG',
        Properties: {
            RouteTableId: cf.ref('MLEnablerRouteTable'),
            DestinationCidrBlock: '0.0.0.0/0',
            GatewayId: cf.ref('MLEnablerInternetGateway')
        }
    },
    MLEnablerSubAAssoc: {
        Type: 'AWS::EC2::SubnetRouteTableAssociation',
        Properties: {
            RouteTableId: cf.ref('MLEnablerRouteTable'),
            SubnetId: cf.ref('MLEnablerSubA')
        }
    },
    MLEnablerSubBAssoc: {
        Type: 'AWS::EC2::SubnetRouteTableAssociation',
        Properties: {
            RouteTableId: cf.ref('MLEnablerRouteTable'),
            SubnetId: cf.ref('MLEnablerSubB')
        }
    },
    MLEnablerNatGateway: {
        Type: 'AWS::EC2::NatGateway',
        DependsOn: 'MLEnablerNatPublicIP',
        Properties:  {
            AllocationId: cf.getAtt('MLEnablerNatPublicIP', 'AllocationId'),
            SubnetId: cf.ref('MLEnablerSubA')
        }
    },
    MLEnablerNatPublicIP: {
        Type: 'AWS::EC2::EIP',
        DependsOn: 'MLEnablerVPC',
        Properties: {
            Domain: 'vpc'
        }
    },
    MLEnablerECSCluster: {
        Type: 'AWS::ECS::Cluster',
        Properties: {
            ClusterName: cf.join('-', [cf.stackName, 'cluster'])
        }
    },
    MLEnablerExecRole: {
        Type: 'AWS::IAM::Role',
        Properties: {
            AssumeRolePolicyDocument: {
                Version: '2012-10-17',
                Statement: [{
                    Effect: 'Allow',
                    Principal: {
                        Service: 'ecs-tasks.amazonaws.com'
                    },
                    Action: 'sts:AssumeRole'
                }]
            },
            Policies: [{
                PolicyName: 'ml-enabler-logging',
                PolicyDocument: {
                    Statement: [{
                        Effect: 'Allow',
                        Action: [
                            'logs:CreateLogGroup',
                            'logs:CreateLogStream',
                            'logs:PutLogEvents',
                            'logs:DescribeLogStreams'
                        ],
                        Resource: [ 'arn:aws:logs:*:*:*' ]
                    }]
                }
            }],
            ManagedPolicyArns: [
                'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
                'arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role',
                'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly'
            ],
            Path: '/service-role/'
        }
    },
    MLEnablerBucket: {
        Type: 'AWS::S3::Bucket',
        Properties: {
            BucketName: cf.join('-', [cf.stackName, cf.accountId, cf.region])
        }
    },
    MLEnablerTaskRole: {
        Type: 'AWS::IAM::Role',
        DependsOn: 'MLEnablerBucket',
        Properties: {
            AssumeRolePolicyDocument: {
                Version: '2012-10-17',
                Statement: [{
                    Effect: 'Allow',
                    Principal: {
                        Service: 'ecs-tasks.amazonaws.com'
                    },
                    Action: 'sts:AssumeRole'
                }]
            },
            Policies: [{
                PolicyName: 'ml-enabler-logging',
                PolicyDocument: {
                    Statement: [{
                        Effect: 'Allow',
                        Action: [
                            'cloudformation:CreateStack',
                            'cloudformation:DeleteStack',
                            'cloudformation:ListStacks',
                            'cloudformation:DescribeStacks',
                            'cloudformation:DescribeStackEvents',
                            'cloudformation:DescribeStackResources'
                        ],
                        Resource: [ cf.join(['arn:aws:cloudformation:', cf.region, ':', cf.accountId,':stack/', cf.stackName, '-*' ])]
                    },{
                        Effect: 'Allow',
                        Action: [
                            'cloudformation:ListStacks'
                        ],
                        Resource: [ '*' ]
                    },{
                        Effect: 'Allow',
                        Action: [
                            's3:GetObject'
                        ],
                        Resource: [ 'arn:aws:s3:::devseed-artifacts/ml-enabler/*' ]
                    },{
                        Effect: 'Allow', // These are all required to spin up a prediction stack
                        Action: [
                            'iam:PassRole',
                            'logs:DescribeLogGroups',
                            'ecs:CreateService',
                            'ecs:DescribeServices',
                            'iam:CreateInstanceProfile',
                            'lambda:GetLayerVersion',
                            'iam:AddRoleToInstanceProfile',
                            'ec2:DescribeInstances',
                            'elasticloadbalancing:AddTags',
                            'autoscaling:CreateLaunchConfiguration',
                            'autoscaling:CreateAutoScalingGroup',
                            'autoscaling:DescribeAutoScalingInstances',
                            'logs:CreateLogGroup',
                            'logs:PutRetentionPolicy',
                            'autoscaling:UpdateAutoScalingGroup',
                            'elasticloadbalancing:DescribeListeners',
                            'elasticloadbalancing:ModifyLoadBalancerAttributes',
                            'autoscaling:DescribeLaunchConfigurations',
                            'lambda:CreateEventSourceMapping',
                            'elasticloadbalancingv2:CreateListener',
                            'elasticloadbalancing:CreateListener',
                            'lambda:GetEventSourceMapping',
                            'ec2:AuthorizeSecurityGroupIngress',
                            'lambda:PutFunctionConcurrency',
                            'sqs:GetQueueAttributes',
                            'elasticloadbalancingv2:CreateTargetGroup',
                            'elasticloadbalancingv2:DescribeTargetGroups',
                            'elasticloadbalancingv2:DescribeLoadBalancers',
                            'elasticloadbalancing:DescribeTargetGroups',
                            'elasticloadbalancing:CreateTargetGroup',
                            'elasticloadbalancing:CreateLoadBalancer',
                            'application-autoscaling:RegisterScalableTarget',
                            'application-autoscaling:PutScalingPolicy',
                            'elasticloadbalancing:DescribeLoadBalancers',
                            'ec2:DescribeAccountAttributes',
                            'ec2:DescribeAddresses',
                            'ec2:DescribeInternetGateways',
                            'ec2:DescribeSecurityGroups',
                            'ec2:DescribeSubnets',
                            'ec2:DescribeVpcs',
                            'iam:CreateServiceLinkedRole',
                            'ec2:CreateSecurityGroup',
                            'sqs:CreateQueue',
                            'sqs:GetQueueAttributes',
                            'lambda:GetFunction',
                            'elasticloadbalancingv2:CreateTargetGroup',
                            'ecs:RegisterTaskDefinition',
                            'lambda:CreateFunction',
                            'ec2:DescribeSecurityGroups'
                        ],
                        Resource: [ '*' ]
                    },{
                        Effect: 'Allow', // And these are required to delete it
                        Action: [
                            'ec2:createTags',
                            'ecs:DeleteService',
                            'ec2:DeleteSecurityGroup',
                            'logs:DeleteLogGroup',
                            'autoscaling:DeleteAutoScalingGroup',
                            'autoscaling:DescribeAutoScalingGroup',
                            'autoscaling:DescribeAutoScalingGroups',
                            'autoscaling:DeleteLaunchConfiguration',
                            'autoscaling:DescribeScalingActivities',
                            'iam:RemoveRoleFromInstanceProfile',
                            'iam:DeleteInstanceProfile',
                            'elasticloadbalancingv2:DeleteLoadBalancer',
                            'elasticloadbalancingv2:DeleteListener',
                            'elasticloadbalancingv2:DeleteTargetGroup',
                            'elasticloadbalancing:DeleteTargetGroup',
                            'elasticloadbalancing:DeleteListener',
                            'elasticloadbalancing:DeleteLoadBalancer',
                            'ec2:DeleteSecurityGroup',
                            'sqs:DeleteQueue',
                            'ecs:DeregisterTaskDefinition',
                            'ecs:UpdateService',
                            'lambda:DeleteFunction',
                            'lambda:DeleteEventSourceMapping',
                            'application-autoscaling:DeregisterScalableTarget',
                            'application-autoscaling:DescribeScalingPolicies',
                            'application-autoscaling:DescribeScalableTargets'
                        ],
                        Resource: [ '*' ]
                    },{
                        Effect: 'Allow',
                        Action: [
                            'sqs:PurgeQueue',
                            'sqs:SendMessage',
                            'sqs:ChangeMessageVisibility',
                            'sqs:ListQueues',
                            'sqs:GetQueueUrl',
                            'sqs:GetQueueAttributes'
                        ],
                        Resource: [ cf.join(['arn:aws:sqs:', cf.region, ':', cf.accountId, ':*']) ]
                    },{
                        Effect: 'Allow',
                        Action: [
                            'batch:SubmitJob',
                            'batch:ListJobs',
                            'batch:DescribeJobs'
                        ],
                        Resource: [ cf.join(['arn:aws:batch:', cf.region, ':', cf.accountId, ':*']) ]
                    },{
                        Effect: 'Allow',
                        Action: [
                            's3:GetObject',
                            's3:DeleteObject',
                            's3:AbortMultipartUpload',
                            's3:GetObjectAcl',
                            's3:ListMultipartUploadParts',
                            's3:PutObject',
                            's3:PutObjectAcl'
                        ],
                        Resource: [ cf.join(['arn:aws:s3:::', cf.ref('MLEnablerBucket'), '/*']) ]
                    }]
                }
            }],
            Path: '/service-role/'
        }
    },
    MLEnablerTaskDefinition: {
        Type: 'AWS::ECS::TaskDefinition',
        DependsOn: 'MLEnablerBucket',
        Properties: {
            Family: cf.stackName,
            Cpu: cf.ref('ContainerCpu'),
            Memory: cf.ref('ContainerMemory'),
            NetworkMode: 'awsvpc',
            RequiresCompatibilities: ['FARGATE'],
            Tags: [{
                Key: 'Name',
                Value: cf.stackName
            }],
            TaskRoleArn: cf.getAtt('MLEnablerTaskRole', 'Arn'),
            ExecutionRoleArn: cf.getAtt('MLEnablerExecRole', 'Arn'),
            ContainerDefinitions: [{
                Name: 'app',
                Image: cf.join([cf.accountId, '.dkr.ecr.', cf.region, '.amazonaws.com/ml-enabler:', cf.ref('GitSha')]),
                PortMappings: [{
                    ContainerPort: 5000
                }],
                Environment: [{
                    Name:'POSTGRES_DB',
                    Value: 'mlenabler'
                },{
                    Name: 'ENVIRONMENT',
                    Value: 'aws'
                },{
                    Name:'POSTGRES_USER',
                    Value: cf.ref('DatabaseUser')
                },{
                    Name:'POSTGRES_PASSWORD',
                    Value: cf.ref('DatabasePassword')
                },{
                    Name:'POSTGRES_ENDPOINT',
                    Value: cf.getAtt('MLEnablerRDS', 'Endpoint.Address')
                },{
                    Name:'POSTGRES_PORT',
                    Value: '5432'
                },{
                    Name: 'FLASK_APP',
                    Value: 'ml_enabler'
                },{
                    Name: 'ECS_LOG_LEVEL',
                    Value: 'debug'
                },{
                    Name: 'GitSha',
                    Value: cf.ref('GitSha')
                },{
                    Name: 'STACK',
                    Value: cf.stackName
                },{
                    Name: 'MAPBOX_TOKEN',
                    Value: cf.ref('MapboxAccessToken')
                },{
                    Name: 'ASSET_BUCKET',
                    Value: cf.ref('MLEnablerBucket')
                }],
                LogConfiguration: {
                    LogDriver: 'awslogs',
                    Options: {
                        'awslogs-group': cf.stackName,
                        'awslogs-region': cf.region,
                        'awslogs-stream-prefix': cf.join('-', ['awslogs', cf.stackName])
                    }
                },
                Essential: true
            }]
        }
    },
    MLEnablerService: {
        Type: 'AWS::ECS::Service',
        Properties: {
            ServiceName: cf.join('-', [cf.stackName, 'Service']),
            Cluster: cf.ref('MLEnablerECSCluster'),
            TaskDefinition: cf.ref('MLEnablerTaskDefinition'),
            LaunchType: 'FARGATE',
            DesiredCount: 1,
            NetworkConfiguration: {
                AwsvpcConfiguration: {
                    AssignPublicIp: 'ENABLED',
                    SecurityGroups: [ cf.ref('MLEnablerServiceSecurityGroup') ],
                    Subnets: [
                        cf.ref('MLEnablerSubA'),
                        cf.ref('MLEnablerSubB')
                    ]
                }
            },
            LoadBalancers: [{
                ContainerName: 'app',
                ContainerPort: 5000,
                TargetGroupArn: cf.ref('MLEnablerTargetGroup')
            }]
        }
    },
    MLEnablerServiceSecurityGroup: {
        Type: 'AWS::EC2::SecurityGroup',
        Properties: {
            GroupDescription: cf.join('-', [cf.stackName, 'ec2-sg']),
            VpcId: cf.ref('MLEnablerVPC'),
            SecurityGroupIngress: [{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 5000,
                ToPort: 5000
            },{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 22,
                ToPort: 22
            }],
            SecurityGroupEgress: [{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 5432,
                ToPort: 5432
            },{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 80,
                ToPort: 80
            },{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 443,
                ToPort: 443
            }]
        }
    },
    MLEnablerTargetGroup: {
        Type: 'AWS::ElasticLoadBalancingV2::TargetGroup',
        Properties: {
            Port: 5000,
            Protocol: 'HTTP',
            VpcId: cf.ref('MLEnablerVPC'),
            TargetType: 'ip',
            Matcher: {
                HttpCode: '200,202,302,304'
            }
        }
    },
    MLEnablerELB: {
        Type: 'AWS::ElasticLoadBalancingV2::LoadBalancer',
        Properties: {
            Name: cf.stackName,
            Type: 'application',
            SecurityGroups: [ cf.ref('MLEnablerELBSecurityGroup') ],
            Subnets: [
                cf.ref('MLEnablerSubA'),
                cf.ref('MLEnablerSubB')
            ]
        }
    },
    MLEnablerELBSecurityGroup: {
        Type: 'AWS::EC2::SecurityGroup',
        Properties: {
            GroupDescription: cf.join('-', [cf.stackName, 'alb-sg']),
            SecurityGroupIngress: [{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 80,
                ToPort: 80
            },{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 443,
                ToPort: 443
            }],
            VpcId: cf.ref('MLEnablerVPC')
        }
    },
    MLEnablerHTTPSListener: {
        Type: 'AWS::ElasticLoadBalancingV2::Listener',
        Condition: 'HasSSL',
        Properties: {
            Certificates: [ {
                CertificateArn: cf.arn('acm', cf.ref('SSLCertificateIdentifier'))
            }],
            DefaultActions: [{
                Type: 'forward',
                TargetGroupArn: cf.ref('MLEnablerTargetGroup')
            }],
            LoadBalancerArn: cf.ref('MLEnablerELB'),
            Port: 443,
            Protocol: 'HTTPS'
        }
    },
    MLEnablerHTTPListenerRedirect: {
        Type: 'AWS::ElasticLoadBalancingV2::Listener',
        Condition: 'HasSSL',
        Properties: {
            DefaultActions: [{
                Type: 'redirect',
                RedirectConfig: {
                    Protocol: 'HTTPS',
                    Port: '443',
                    Host: '#{host}',
                    Path: '/#{path}',
                    Query: '#{query}',
                    StatusCode: 'HTTP_301'
                }
            }],
            LoadBalancerArn: cf.ref('MLEnablerELB'),
            Port: 80,
            Protocol: 'HTTP'
        }
    },
    MLEnablerHTTPListener: {
        Type: 'AWS::ElasticLoadBalancingV2::Listener',
        Condition: 'HasNoSSL',
        Properties: {
            DefaultActions: [{
                Type: 'forward',
                TargetGroupArn: cf.ref('MLEnablerTargetGroup')
            }],
            LoadBalancerArn: cf.ref('MLEnablerELB'),
            Port: 80,
            Protocol: 'HTTP'
        }
    },
    MLEnablerRDS: {
        Type: 'AWS::RDS::DBInstance',
        Properties: {
            Engine: 'postgres',
            DBName: 'mlenabler',
            EngineVersion: '11.6',
            MasterUsername: cf.ref('DatabaseUser'),
            MasterUserPassword: cf.ref('DatabasePassword'),
            AllocatedStorage: 10,
            MaxAllocatedStorage: 100,
            BackupRetentionPeriod: 10,
            StorageType: 'gp2',
            DBInstanceClass: cf.ref('DatabaseType'),
            DBSecurityGroups: [ cf.ref('MLEnablerRDSSecurityGroup') ],
            DBSubnetGroupName: cf.ref('MLEnablerRDSSubnet'),
            PubliclyAccessible: true
        }
    },
    MLEnablerRDSSubnet: {
        Type: 'AWS::RDS::DBSubnetGroup',
        Properties: {
            DBSubnetGroupDescription: cf.join('-', [cf.stackName, 'rds-subnets']),
            SubnetIds: [
                cf.ref('MLEnablerSubA'),
                cf.ref('MLEnablerSubB')
            ]
        }
    },
    MLEnablerRDSSecurityGroup: {
        Type: 'AWS::RDS::DBSecurityGroup',
        Properties: {
            GroupDescription: cf.join('-', [cf.stackName, 'rds-sg']),
            EC2VpcId: cf.ref('MLEnablerVPC'),
            DBSecurityGroupIngress: [{
                EC2SecurityGroupId: cf.getAtt('MLEnablerServiceSecurityGroup', 'GroupId')
            },{
                  CIDRIP: '0.0.0.0/0'
            }]
        }
    },
    PredLambdaFunctionRole: {
        Type: 'AWS::IAM::Role',
        Properties: {
            RoleName: cf.join('-', [ cf.ref('AWS::StackName'), 'queue-role' ]),
            AssumeRolePolicyDocument: {
                Version: '2012-10-17',
                Statement: [{
                    Effect: 'Allow',
                    Principal: {
                        Service: 'lambda.amazonaws.com'
                    },
                    Action: 'sts:AssumeRole'
                }]
            },
            Path: '/',
            Policies: [{
                PolicyName: cf.join('-', [ cf.ref('AWS::StackName'), 'queue-policy' ]),
                PolicyDocument: {
                    Version: '2012-10-17',
                    Statement: [{
                        Effect: 'Allow',
                        Action: [
                            'lambda:GetFunction',
                            'lambda:invokeFunction',
                            'logs:CreateLogGroup',
                            'logs:CreateLogStream',
                            'logs:DescribeLogStreams',
                            'logs:PutLogEvents'
                        ],
                        Resource: '*'
                    },{
                        Effect: 'Allow',
                        Action: [
                            'sqs:SendMessage',
                            'sqs:ReceiveMessage',
                            'sqs:ChangeMessageVisibility',
                            'sqs:DeleteMessage',
                            'sqs:GetQueueUrl',
                            'sqs:GetQueueAttributes'
                        ],
                        Resource: '*'
                    }]
                }
            }]
        }
    },
    PredServiceScalingRole: {
        Type: 'AWS::IAM::Role',
        Properties: {
            AssumeRolePolicyDocument: {
                Statement: [{
                    Effect: 'Allow',
                    Principal: {
                        Service: ['application-autoscaling.amazonaws.com']
                    },
                    Action: ['sts:AssumeRole']
                }]
            },
            Path: '/',
            Policies: [{
                PolicyName: 'mlservice-autoscaling',
                PolicyDocument: {
                    Statement: [{
                        Effect: 'Allow',
                        Action: [
                            'application-autoscaling:*',
                            'cloudwatch:DescribeAlarms',
                            'cloudwatch:PutMetricAlarm',
                            'ecs:DescribeServices',
                            'ecs:UpdateService'
                        ],
                        Resource: '*'
                    }]
                }
            }]
        }
    },
    PredExecRole: {
        Type: 'AWS::IAM::Role',
        Properties: {
            AssumeRolePolicyDocument: {
                Version: '2012-10-17',
                Statement: [{
                    Effect: 'Allow',
                    Principal: {
                        Service: [
                            'ec2.amazonaws.com',
                            'ecs.amazonaws.com',
                            'ecs-tasks.amazonaws.com'
                        ]
                    },
                    Action: 'sts:AssumeRole'
                }]
            },
            Policies: [{
                PolicyName: 'ml-enabler-pred-logging',
                PolicyDocument: {
                    Statement: [{
                        Effect: 'Allow',
                        Action: [
                            'logs:CreateLogGroup',
                            'logs:CreateLogStream',
                            'logs:PutLogEvents',
                            'logs:DescribeLogStreams'
                        ],
                        Resource: [ 'arn:aws:logs:*:*:*' ]
                    },{
                        Effect: 'Allow',
                        Action: [
                            'elasticloadbalancing:*'
                        ],
                        Resource: '*'
                    }]
                }
            }],
            ManagedPolicyArns: [
                'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
                'arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role',
                'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly'
            ],
            Path: '/service-role/'
        }
    },
    PredTaskRole: {
        Type: 'AWS::IAM::Role',
        Properties: {
            AssumeRolePolicyDocument: {
                Version: '2012-10-17',
                Statement: [{
                    Effect: 'Allow',
                    Principal: {
                        Service: 'ecs-tasks.amazonaws.com'
                    },
                    Action: 'sts:AssumeRole'
                }]
            },
            Path: '/service-role/'
        }
    },
    PredServiceSecurityGroup: {
        Type : 'AWS::EC2::SecurityGroup',
        Properties: {
            GroupDescription: cf.join('-', [
                cf.ref('AWS::StackName'),
                'pred-ec2-sg'
            ]),
            VpcId: cf.ref('MLEnablerVPC'),
            SecurityGroupIngress: [{
                CidrIp: '0.0.0.0/0',
                IpProtocol: 'tcp',
                FromPort: 8501,
                ToPort: 8501
            }]
        }
    }
};

const Mappings = {
    AWSRegion2AZ: {
        'us-east-1': { '1': 'us-east-1b', '2': 'us-east-1c', '3': 'us-east-1d', '4': 'us-east-1e' },
        'us-west-1': { '1': 'us-west-1b', '2': 'us-west-1c' },
        'us-west-2': { '1': 'us-west-2a', '2': 'us-west-2b', '3': 'us-west-2c'  }
    }
}

const Conditions = {
    HasSSL: cf.notEquals(cf.ref('SSLCertificateIdentifier'), ''),
    HasNoSSL: cf.equals(cf.ref('SSLCertificateIdentifier'), '')
}

const Outputs = {
    InternalServiceSG: {
        Description: 'Service SG',
        Value: cf.ref('PredServiceSecurityGroup'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'sg'])
        }
    },
    InternalLambdaRole: {
        Description: 'Lambda Function Role',
        Value: cf.getAtt('PredLambdaFunctionRole', 'Arn'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'lambda-role'])
        }
    },
    InternalScalingRole: {
        Description: 'Scaling Role',
        Value: cf.getAtt('PredServiceScalingRole', 'Arn'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'scaling-role'])
        }
    },
    InternalExecRoleARN: {
        Description: 'Container Exec Role',
        Value: cf.getAtt('PredExecRole', 'Arn'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'exec-role-arn'])
        }
    },
    InternalExecRoleName: {
        Description: 'Container Exec Role',
        Value: cf.ref('PredExecRole'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'exec-role-name'])
        }
    },
    InternalTaskRole: {
        Description: 'Container Exec Role',
        Value: cf.getAtt('PredTaskRole', 'Arn'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'task-role'])
        }
    },
    InternalVPC: {
        Description: 'The ARN of the VPC',
        Value: cf.ref('MLEnablerVPC'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'vpc'])
        }
    },
    InternalCluster: {
        Description: 'The ARN of the Cluster',
        Value: cf.ref('MLEnablerECSCluster'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'cluster'])
        }
    },
    InternalSubA: {
        Description: 'SubnetA',
        Value: cf.ref('MLEnablerSubA'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'suba'])
        }
    },
    InternalSubB: {
        Description: 'SubnetA',
        Value: cf.ref('MLEnablerSubB'),
        Export: {
            Name: cf.join('-', [cf.stackName, 'subb'])
        }
    },
    API: {
        Description: 'API URL',
        Value: cf.join(['http://', cf.getAtt('MLEnablerELB', 'DNSName')]),
        Export: {
            Name: cf.join('-', [cf.stackName, 'api'])
        }
    },
    UI: {
        Description: 'UI URL',
        Value: cf.join(['http://', cf.getAtt('MLEnablerELB', 'DNSName'), '/admin/'])
    },
    S3: {
        Description: 'Asset Storage',
        Value: cf.ref('MLEnablerBucket')
    },
    DB: {
        Description: 'Postgres Connection String',
        Value: cf.join([
            'postgresql://',
            cf.ref('DatabaseUser'),
            ':',
            cf.ref('DatabasePassword'),
            '@',
            cf.getAtt('MLEnablerRDS', 'Endpoint.Address'),
            ':5432/mlenabler'
        ])
    }
};

module.exports = cf.merge({
    Parameters,
    Resources,
    Mappings,
    Conditions,
    Outputs
}, batch);
