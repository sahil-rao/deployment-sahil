#Sets up Ansible, Runs Ansible
echo "Installling Hive"
sudo rm -rf /usr/lib/hive
sudo tar -zxf /home/xplain/apache-hive-0.13.0-SNAPSHOT-bin.tar.gz -C /home/xplain
sudo mv /home/xplain/apache-hive-0.13.0-SNAPSHOT-bin /usr/lib/hive
echo "Running playbook vm-update.yml"
sudo ansible-playbook vm-update.yml --connection=local
python /home/xplain/setupSilo.py
echo "Running playbook vm-hadoop.yml"
#commenting till we figure out were to copy tar ball for impala
#sudo ansible-playbook vm-hadoop.yml --connection=local
sudo ./refresh.sh
exit 0
