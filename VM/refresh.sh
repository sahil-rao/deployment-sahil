#Restarts running services 
sudo mongod --fork --logpath /mnt/volume1/mongo/log/mongo.log -dbpath /mnt/volume1/mongo/db 
sudo service baazdataacquisition restart                               
sudo service baazcompile restart  
sudo service baazmath restart  
sudo stop nodejs                                 
sudo start nodejs  
sudo monit                               
exit 0
