# How to Delete an Existing VCN

1. Select the VCN and try **Delete All** first.
2. If it fails, delete the related resources manually in the following order:

```text
Instance / Load Balancer / DB and other resources
                ↓
               VNIC
                ↓
              Subnet
                ↓
             Route Rules
   (Internet Gateway / NAT Gateway / Service Gateway)
                ↓
       Other custom network resources
                ↓
               VCN
```

The network structure can be roughly understood as:

```text
VCN
    │
    └── Subnet
         │
         └── VNIC
              │
              └── Instance
```
