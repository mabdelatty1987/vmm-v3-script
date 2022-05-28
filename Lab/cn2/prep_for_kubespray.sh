sudo apt -y update && sudo apt -y upgrade
sudo apt -y  install python3-pip
git clone https://github.com/kubernetes-incubator/kubespray.git
sudo apt -y remove python3-jinja2 python3-cryptography python3-markupsafe && sudo apt autoremove -y 
cd kubespray
sudo pip install -r requirements.txt
cp -rfp inventory/sample inventory/mycluster
