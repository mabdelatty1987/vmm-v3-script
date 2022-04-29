#!/bin/bash
cat > /var/tmp/npatpw <<EOF
expire_date=6/7/2024
usercount=5
node_limit=250
card=micro_service
MAC=FF:EE:DD:CC:BB:AA
customer=MICRO_SERVICE
S-NS-PLNR-BSC=gWTqDmZKRnaQRVjARguWYW
S-NS-PLNR-PRM=TWRhUihDeZLWDYFXDbiaTj
S-NS-SDN-BSC=ZIVamtZDhiHQRVjARguWYW
S-NS-SDN-STD=LDYYjugBUpZLSBGTOimXQn
S-NS-SDN-PRM=gdPdcxcSjjXRYWYPDauiBD
EOF
sudo mv /etc/kubernetes/po/ns-common/npatpw ~/npatpw.backup
sudo cp /var/tmp/npatpw  /etc/kubernetes/po/ns-common/npatpw
kubectl -n northstar delete secret northstar-license
kubectl -n northstar create secret generic northstar-license --from-file /etc/kubernetes/po/ns-common/npatpw
kubectl -n northstar get secret northstar-license
