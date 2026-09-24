# 如何删除已存在的 VCN

1. 选择 VCN 后尝试 Delate All
2. 如果失败遵循以下顺序一个个删：
```
Instance / Load Balancer / DB 等资源
                ↓
               VNIC
                ↓
              Subnet
                ↓
             Route Rules（Internet Gateway / NAT Gateway / Service Gateway）
                ↓
          其他自定义网络资源
                ↓
               VCN
```

网络大致结构：
```
VCN
    │
    └── Subnet
         │
         └── VNIC
              │
              └── Instance
```
