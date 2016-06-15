#Restarts stateful services (mongodb and elasticsearch) 
sudo mongod --fork --logpath /mnt/volume1/mongo/log/mongo.log -dbpath /mnt/volume1/mongo/db 
sudo service elasticsearch restart

# Restart java compilers
sudo stop advanalytics_compiler 
sudo start advanalytics_compiler
sudo stop compileservice_compiler 
sudo start compileservice_compiler 
sudo stop applicationservice_compiler 
sudo start applicationservice_compiler

# Restart python services
sudo stop dataacquisitionservice
sudo start dataacquisitionservice
sudo stop compileservice
sudo start compileservice 
sudo stop mathservice 
sudo start mathservice 
sudo stop advanalytics
sudo start advanalytics
sudo stop applicationservice
sudo start applicationservice
sudo stop ruleengineservice
sudo start ruleengineservice
sudo stop elasticpub
sudo start elasticpub

# Restart node processes
sudo stop nodejs                                 
sudo start nodejs  
sudo stop api_nodejs
sudo start api_nodejs

#sudo monit                               
exit 0
