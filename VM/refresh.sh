#Restarts running services 
sudo mongod --fork --logpath /mnt/volume1/mongo/log/mongo.log -dbpath /mnt/volume1/mongo/db 
sudo service baazdataacquisition restart                               
sudo service baazcompile restart  
sudo stop nodejs                                 
sudo start nodejs                                 
exit 0
