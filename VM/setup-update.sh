#Sets up Ansible, Runs Ansible
echo "Installling Hive"
sudo rm -rf /usr/lib/hive
sudo tar -zxf /home/ubuntu/apache-hive-0.13.0-SNAPSHOT-bin.tar.gz -C /home/ubuntu
sudo mv /home/ubuntu/apache-hive-0.13.0-SNAPSHOT-bin /usr/lib/hive
echo "Running playbook vm-update.yml"
sudo ansible-playbook vm-update.yml --connection=local
sudo ./refresh.sh
exit 0
