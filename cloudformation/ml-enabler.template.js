const cf = require("@mapbox/cloudfriend");
const tfserving = require('./tfserving');

const Parameters = {
    ImageTag: {
        Description: "The tag for the docker hub image",
        Type: "String"
    },
    ContainerCpu: {
        Description: "How much CPU to give to the container. 1024 is 1 cpu. See aws docs for acceptable cpu/mem combinations",
        Default: 1024,
        Type: "Number"
    },
    ContainerMemory: {
        Description: "How much memory in megabytes to give to the container. See aws docs for acceptable cpu/mem combinations",
        Default: 1024,
        Type: "Number"
    },
    SSLCertificateIdentifier: {
        Type: 'String',
        Description: 'SSL certificate for HTTPS protocol'
    },
    DatabaseUser: {
        Type: "String",
        Description: "Database Username"
    },
    DatabasePassword: {
        Type: "String",
        Description: "Database User Password"
    }
};

const Resources = {
    MLEnablerVPC: {
        "Type" : "AWS::EC2::VPC",
        "Properties" : {
            "CidrBlock" : "10.1.0.0/16"
        }
    },
    MLEnablerSubA: {
        "Type" : "AWS::EC2::Subnet",
        "Properties" : {
            VpcId: cf.ref('MLEnablerVPC'),
            CidrBlock: "10.1.10.0/24"
        }
    },
    MLEnablerSubB: {
        "Type" : "AWS::EC2::Subnet",
        "Properties" : {
            VpcId: cf.ref('MLEnablerVPC'),
            CidrBlock: "10.1.20.0/24"
        }
    },
    MLEnablerECSCluster: {
        Type: "AWS::ECS::Cluster",
        Properties: {
            ClusterName: cf.join("-", [cf.stackName, "cluster"])
        }
    },
    MLEnablerTaskDefinition: {
        Type: "AWS::ECS::TaskDefinition",
        Properties: {
            Family: cf.stackName,
            Cpu: cf.ref("ContainerCpu"),
            Memory: cf.ref("ContainerMemory"),
            NetworkMode: "awsvpc",
            RequiresCompatibilities: ["FARGATE"],
            Tags: [{
                Key: "Name",
                Value: cf.stackName
            }],
            ContainerDefinitions: [{
                Name: "app",
                Image: cf.join(":", ["hotosm/ml-enabler", cf.ref("ImageTag")]),
                PortMappings: [{
                    ContainerPort: 5000
                }],
                Environment: [{
                    Name:"POSTGRES_DB",
                    Value: 'mlenabler'
                },{
                    Name:"POSTGRES_USER",
                    Value: cf.ref("DatabaseUser")
                },{
                    Name:"POSTGRES_PASSWORD",
                    Value: cf.ref("DatabasePassword")
                },{
                    Name:"POSTGRES_ENDPOINT",
                    Value: cf.getAtt("MLEnablerRDS", "Endpoint.Address")
                },{
                    Name:"POSTGRES_PORT",
                    Value: "5432"
                },{
                    Name: "FLASK_APP",
                    Value: "ml_enabler"
                },{
                    Name: "ECS_LOG_LEVEL",
                    Value: "debug"
                }],
                LogConfiguration: {
                    LogDriver: "awslogs",
                    Options: {
                        "awslogs-group": cf.join("-", ["awslogs", cf.stackName]),
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": cf.join("-", ["awslogs", cf.stackName])
                    }
                },
                Essential: true
            },{
                Name: "migration",
                Image: cf.join(":", ["hotosm/ml-enabler", cf.ref("ImageTag")]),
                Environment: [{
                    Name:"POSTGRES_DB",
                    Value: 'mlenabler'
                },{
                    Name:"POSTGRES_USER",
                    Value: cf.ref("DatabaseUser")
                },{
                    Name:"POSTGRES_PASSWORD",
                    Value: cf.ref("DatabasePassword")
                },{
                    Name:"POSTGRES_ENDPOINT",
                    Value: cf.getAtt("MLEnablerRDS", "Endpoint.Address")
                },{
                    Name:"POSTGRES_PORT",
                    Value: "5432"
                },{
                    Name: "FLASK_APP",
                    Value: "ml_enabler"
                }],
                PortMappings: [{
                    ContainerPort: 5432
                }],
                Command: ["flask","db", "upgrade"],
                Essential: false
            }]
        }
    },
    MLEnablerService: {
        Type: "AWS::ECS::Service",
        Properties: {
            ServiceName: cf.join("-", [cf.stackName, "Service"]),
            Cluster: cf.ref("MLEnablerECSCluster"),
            TaskDefinition: cf.ref("MLEnablerTaskDefinition"),
            LaunchType: "FARGATE",
            HealthCheckGracePeriodSeconds: 300,
            DesiredCount: 1,
            NetworkConfiguration: {
                AwsvpcConfiguration: {
                    AssignPublicIp: "ENABLED",
                    SecurityGroups: cf.ref('MLEnablerServiceSecurityGroup'),
                    Subnets: [
                        cf.ref('MLEnablerSubA'),
                        cf.ref('MLEnablerSubB')
                    ]
                }
            },
            LoadBalancers: [{
                ContainerName: "app",
                ContainerPort: 5000,
                TargetGroupArn: cf.ref("MLEnablerTargetGroup")
            }]
        }
    },
    MLEnablerServiceSecurityGroup: {
        "Type" : "AWS::EC2::SecurityGroup",
        "Properties" : {
            GroupDescription: cf.join("-", [cf.stackName, "ec2-sg"]),
            VpcId: cf.ref('MLEnablerVPC')
        }
    },
    MLEnablerTargetGroup: {
        Type: "AWS::ElasticLoadBalancingV2::TargetGroup",
        Properties: {
            Port: 5000,
            Protocol: "HTTP",
            VpcId: cf.ref('MLEnablerVPC'),
            TargetType: "ip",
            Matcher: {
                HttpCode: "200,202,302,304"
            }
        }
    },
    MLEnablerALB: {
        Type: "AWS::ElasticLoadBalancingV2::LoadBalancer",
        Properties: {
            Name: cf.stackName,
            Type: "application",
            SecurityGroups: [ cf.ref('MLEnablerALBSecurityGroup') ],
            Subnets: [
                cf.ref('MLEnablerSubA'),
                cf.ref('MLEnablerSubB')
            ]
        }
    },
    MLEnablerALBSecurityGroup: {
        "Type" : "AWS::EC2::SecurityGroup",
        "Properties" : {
            GroupDescription: cf.join("-", [cf.stackName, "alb-sg"]),
            VpcId: cf.ref('MLEnablerVPC')
        }
    },
    MLEnablerHTTPSListener: {
        Type: 'AWS::ElasticLoadBalancingV2::Listener',
        Properties: {
            Certificates: [ {
                CertificateArn: cf.arn('acm', cf.ref('SSLCertificateIdentifier'))
            }],
            DefaultActions: [{
                Type: 'forward',
                TargetGroupArn: cf.ref('MLEnablerTargetGroup')
            }],
            LoadBalancerArn: cf.ref('MLEnablerALB'),
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
            LoadBalancerArn: cf.ref('MLEnablerALB'),
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
            MasterUsername: cf.ref("DatabaseUser"),
            MasterUserPassword: cf.ref("DatabasePassword"),
            AllocatedStorage: 10,
            MaxAllocatedStorage: 100,
            BackupRetentionPeriod: 10,
            StorageType: 'gp2',
            DBInstanceClass: 'db.m4.xlarge',
            DBSecurityGroupIngress: [ cf.ref('MLEnablerRDSSecurityGroup') ]
        }
    },
    "MLEnablerRDSSecurityGroup": {
        Type : "AWS::RDS::DBSecurityGroup",
        Properties : {
            GroupDescription: cf.join("-", [cf.stackName, "rds-sg"]),
            DBSecurityGroupIngress : [ cf.ref('MLEnablerRDSSecurityGroupIngress') ]
        }
    },
    MLEnablerRDSSecurityGroupIngress: {
        Type : "AWS::RDS::DBSecurityGroupIngress",
        Properties : {
            DBSecurityGroupName: cf.join("-", [cf.stackName, "rds-sg-ingress"]),
            EC2SecurityGroupName : cf.ref('MLEnablerServiceSecurityGroup')
        }
    }
};

//module.exports = cf.merge({ Parameters, Resources }, tfserving;
module.exports = { Parameters, Resources };
