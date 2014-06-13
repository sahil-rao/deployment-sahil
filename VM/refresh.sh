#Restarts running services 
sudo mongod --fork --logpath /mnt/volume1/mongo/log/mongo.log -dbpath /mnt/volume1/mongo/db 
sudo stop dataacquisitionservice
sudo start dataacquisitionservice
sudo stop compileservice 
sudo stop compileserver 
sudo start compileserver 
sudo start compileservice 
sudo stop mathservice 
sudo start mathservice 
sudo stop nodejs                                 
sudo start nodejs  
sudo monit                               
exit 0
