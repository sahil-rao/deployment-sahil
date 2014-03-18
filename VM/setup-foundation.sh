#Sets up Ansible, Runs Ansible
echo "Installling Hive"
sudo tar -zxf /home/ubuntu/apache-hive-0.13.0-SNAPSHOT-bin.tar.gz -C /home/ubuntu
sudo mv /home/ubuntu/apache-hive-0.13.0-SNAPSHOT-bin /usr/lib/hive
echo "Installed Hive"
echo "Making directories..."
sudo mkdir /var/Baaz
sudo cp hosts.cfg /var/Baaz
sudo cp ga.cfg /var/Baaz
sudo chmod a+r /var/Baaz/hosts.cfg
sudo chmod a+r /var/Baaz/ga.cfg
sudo add-apt-repository ppa:rquillo/ansible
echo "Adding Ansible Repository"
sudo apt-get -y update
echo "Installing Ansible"
sudo apt-get -y install ansible
echo "Copying hosts inventory file"
sudo cp hosts /etc/ansible/
echo "Running playbook site.yml"
sudo ansible-playbook vm-foundation.yml --connection=local
exit 0
