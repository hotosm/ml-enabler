const cf = require('@mapbox/cloudfriend');
const tfserving = require('./tfserving');

const Parameters = {
    ImageTag: {
        Description: 'The tag for the docker hub image',
        Type: 'String'
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
    DatabaseUser: {
        Type: 'String',
        Description: 'Database Username'
    },
    DatabasePassword: {
        Type: 'String',
        Description: 'Database User Password'
    }
};

const Resources = {
    MLEnablerVPC: {
        'Type' : 'AWS::EC2::VPC',
        'Properties' : {
            'CidrBlock' : '10.1.0.0/16'
        }
    },
    MLEnablerSubA: {
        'Type' : 'AWS::EC2::Subnet',
        'Properties' : {
            AvailabilityZone: cf.findInMap('AWSRegion2AZ', cf.region, '1'),
            VpcId: cf.ref('MLEnablerVPC'),
            CidrBlock: '10.1.10.0/24'
        }
    },
    MLEnablerSubB: {
        'Type' : 'AWS::EC2::Subnet',
        'Properties' : {
            AvailabilityZone: cf.findInMap('AWSRegion2AZ', cf.region, '2'),
            VpcId: cf.ref('MLEnablerVPC'),
            CidrBlock: '10.1.20.0/24'
        }
    },
    MLEnablerInternetGateway: {
        'Type' : 'AWS::EC2::InternetGateway'
    },
    MLEnablerVPCIG: {
        'Type' : 'AWS::EC2::VPCGatewayAttachment',
        'Properties' : {
            'InternetGatewayId' : cf.ref('MLEnablerInternetGateway'),
            'VpcId' : cf.ref('MLEnablerVPC')
        }
    },
    MLEnablerRouteTable: {
        'Type' : 'AWS::EC2::RouteTable',
        'Properties' : {
            'VpcId' : cf.ref('MLEnablerVPC')
        }
    },
    MLEnablerSubAAssoc: {
        'Type' : 'AWS::EC2::SubnetRouteTableAssociation',
        'Properties' : {
            'RouteTableId': cf.ref('MLEnablerRouteTable'),
            'SubnetId': cf.ref('MLEnablerSubA')
        }
    },
    MLEnablerSubBAssoc: {
        'Type' : 'AWS::EC2::SubnetRouteTableAssociation',
        'Properties' : {
            'RouteTableId': cf.ref('MLEnablerRouteTable'),
            'SubnetId': cf.ref('MLEnablerSubB')
        }
    },
    MLEnablerECSCluster: {
        Type: 'AWS::ECS::Cluster',
        Properties: {
            ClusterName: cf.join('-', [cf.stackName, 'cluster'])
        }
    },
    MLEnablerTaskRole: {
        'Type': 'AWS::IAM::Role',
        'Properties': {
            'AssumeRolePolicyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': 'ec2.amazonaws.com'
                    },
                    'Action': 'sts:AssumeRole'
                }]
            },
            'ManagedPolicyArns': [ 'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy' ],
            'Path': '/service-role/'
        }
    },
    MLEnablerTaskDefinition: {
        Type: 'AWS::ECS::TaskDefinition',
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
            ExecutionRoleArn: cf.getAtt('MLEnablerTaskRole', 'Arn'),
            ContainerDefinitions: [{
                Name: 'app',
                Image: cf.join(':', ['hotosm/ml-enabler', cf.ref('ImageTag')]),
                PortMappings: [{
                    ContainerPort: 5000
                }],
                Environment: [{
                    Name:'POSTGRES_DB',
                    Value: 'mlenabler'
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
                }],
                LogConfiguration: {
                    LogDriver: 'awslogs',
                    Options: {
                        'awslogs-group': cf.join('-', ['awslogs', cf.stackName]),
                        'awslogs-region': 'us-east-1',
                        'awslogs-stream-prefix': cf.join('-', ['awslogs', cf.stackName])
                    }
                },
                Essential: true
            },{
                Name: 'migration',
                Image: cf.join(':', ['hotosm/ml-enabler', cf.ref('ImageTag')]),
                Environment: [{
                    Name:'POSTGRES_DB',
                    Value: 'mlenabler'
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
                }],
                PortMappings: [{
                    ContainerPort: 5432
                }],
                Command: ['flask','db', 'upgrade'],
                Essential: false
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
            HealthCheckGracePeriodSeconds: 300,
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
        'Type' : 'AWS::EC2::SecurityGroup',
        'Properties' : {
            GroupDescription: cf.join('-', [cf.stackName, 'ec2-sg']),
            VpcId: cf.ref('MLEnablerVPC')
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
        'Type' : 'AWS::EC2::SecurityGroup',
        'Properties' : {
            GroupDescription: cf.join('-', [cf.stackName, 'alb-sg']),
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
    MLEnablerHTTPListener: {
        Type: 'AWS::ElasticLoadBalancingV2::Listener',
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
    MLEnablerRDS: {
        Type: 'AWS::RDS::DBInstance',
        Properties: {
            Engine: 'postgres',
            DBName: 'mlenabler',
            EngineVersion: '11.2',
            MasterUsername: cf.ref('DatabaseUser'),
            MasterUserPassword: cf.ref('DatabasePassword'),
            AllocatedStorage: 10,
            MaxAllocatedStorage: 100,
            BackupRetentionPeriod: 10,
            StorageType: 'gp2',
            DBInstanceClass: 'db.m4.xlarge',
            DBSecurityGroups: [ cf.ref('MLEnablerRDSSecurityGroup') ],
            DBSubnetGroupName: cf.ref('MLEnablerRDSSubnet')
        }
    },
    MLEnablerRDSSubnet: {
        'Type' : 'AWS::RDS::DBSubnetGroup',
        'Properties' : {
            'DBSubnetGroupDescription': cf.join('-', [cf.stackName, 'rds-subnets']),
            'SubnetIds': [
                cf.ref('MLEnablerSubA'),
                cf.ref('MLEnablerSubB')
            ]
        }
    },
    'MLEnablerRDSSecurityGroup': {
        Type : 'AWS::RDS::DBSecurityGroup',
        Properties : {
            GroupDescription: cf.join('-', [cf.stackName, 'rds-sg']),
            EC2VpcId: cf.ref('MLEnablerVPC'),
            DBSecurityGroupIngress: {
                EC2SecurityGroupId: cf.getAtt('MLEnablerServiceSecurityGroup', 'GroupId')
            }
        }
    }
};

const Mappings = {
    'AWSRegion2AZ' : {
        'us-east-1' : { '1' : 'us-east-1b', '2' : 'us-east-1c', '3' : 'us-east-1d', '4' : 'us-east-1e' },
        'us-west-1' : { '1' : 'us-west-1b', '2' : 'us-west-1c' },
        'us-west-2' : { '1' : 'us-west-2a', '2' : 'us-west-2b', '3' : 'us-west-2c'  }
    }
}

const Conditions = {
    HasSSL: cf.notEquals(cf.ref('SSLCertificateIdentifier'), '')
}

const ml = {
    Parameters,
    Resources,
    Mappings,
    Conditions
};

module.exports = ml;
//module.exports = cf.merge(ml, tfserving);
