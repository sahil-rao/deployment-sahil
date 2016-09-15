var gulp = require('gulp'),
    gulpConfig = require('./gulp-config'),
    jshint = require('gulp-jshint'),
    packageJSON  = require('./package'),
    webpack = require('webpack-stream'),
    scp = require('gulp-scp2'),
    fs = require('fs-extra'),
    fsj = require('fs-jetpack'),
    buffer = require('vinyl-buffer'),
    tar = require('gulp-tar'),
    Ssh = require('gulp-ssh'),
    args = require('yargs').argv,
    Git = require("nodegit"),
    prompt = require("prompt"),
    Q = require('q'),
    gulpSequence = require('gulp-sequence'), //Remove this once we upgrade to gulp 4.0
    gzip = require('gulp-gzip');

var branch = args.branch || 'master';

gulp.task('purge-ui', function(){
  console.log("Cleaning UI directory");
  var deferred = Q.defer();
  fs.remove(gulpConfig.uiDir, function(err){
    if(err){
      throw err;
    }
    deferred.resolve();
  });

  return deferred.promise;
});

gulp.task('pull-latest', ['purge-ui'], function(){
  console.log("Pulling latest UI code");

  return gitHubLogin().then(function(input){
    var deffered = Q.defer();
    var opts = {
      checkoutBranch: branch,
      fetchOpts: {
        callbacks: {
          credentials: function() {
            return Git.Cred.userpassPlaintextNew(input.user, input.pw);
          }
        }
      }
    };
    deffered.resolve(opts);
    return deffered.promise;
  })
  .then(function(opts){
    return Git.Clone(gulpConfig.gitUrl+"UI.git", gulpConfig.uiDir, opts); //Git Clone returns a promise
  });
});

gulp.task('webpack-build', function(cb){
  console.log("Compiling code");
  var dir = gulpConfig.uiDir+'xplain.io/';
  fs.copySync(dir+'src/index.html', dir+'build/index.html');
  return gulp.src(dir+'src/main.js')
    .pipe(webpack(require('./webpack.config.js')(dir) ))
    .pipe(gulp.dest(dir+'build/'));
});

/*
Build main application
*/
gulp.task('app-build', ["webpack-build"], function(){
  console.log("Building app");
  var dir = gulpConfig.uiDir;
  try{
    var dest = fsj.dir(dir+'/tmp/xplain.io/xplain.io', {empty:true});
    fsj.copy(dir+'/xplain.io', dest.path(), {
      overwrite:true,
      matching: ['!node_modules/**']
    });
    fs.removeSync(dir+'/tmp/xplain.io/xplain.io/node_modules');
    return gulp.src(dir+'/tmp/xplain.io/**')
        .pipe(tar('xplain.io.tar'))
        .pipe(gzip())
        .pipe(gulp.dest(dir))
        .on('error', function(err){
          console.log(err);
        })
        .on('end', function(){
          console.log("End");
          fs.remove(dir+'/tmp/xplain.io');
        });
  }
  catch(e){
    console.error(e);
  }
});

/*
Build admin application
*/

gulp.task('admin-build', function(){
  var dir = gulpConfig.uiDir;
  try{
    var dest = fsj.dir(dir+'/tmp/optimizer_admin/optimizer_admin', {empty:true});
    fsj.copy(dir+'/optimizer_admin', dest.path(), {
      overwrite:true,
      matching: ['!node_modules/**']
    });
    fs.removeSync(dir+'/tmp/optimizer_admin/optimizer_admin/node_modules');
    return gulp.src(dir+'/tmp/optimizer_admin/**')
        .pipe(tar('optimizer_admin.tar'))
        .pipe(gzip())
        .pipe(gulp.dest(dir))
        .on('error', function(err){
          console.log(err);
        })
        .on('end', function(){
          console.log("End");
          fs.remove(dir+'/tmp/optimizer_admin');
        });
  }
  catch(e){
    console.error(e);
  }
});

gulp.task('api-build', function(){
  console.log("Building api");
  var dir = gulpConfig.uiDir;
  try{
    var dest = fsj.dir(dir+'/tmp/optimizer_api/optimizer_api', {empty:true});
    fsj.copy(dir+'/optimizer_api', dest.path(), {
      overwrite:true,
      matching: ['!node_modules/**']
    });
    fs.removeSync(dir+'/tmp/optimizer_api/optimizer_api/node_modules');
    return gulp.src(dir+'/tmp/optimizer_api/**')
        .pipe(tar('optimizer_api.tar'))
        .pipe(gzip())
        .pipe(gulp.dest(dir))
        .on('error', function(err){
          console.log(err);
        })
        .on('end', function(){
          console.log("End");
          fs.remove(dir+'/tmp/optimizer_api');
        });
  }
  catch(e){
    console.error(e);
  }
});

gulp.task('test-build', function(){

});

//gulp.task('full-build', gulpSequence('pull-latest', ['app-build', 'test-build', 'api-build', 'admin-build']));
gulp.task('full-build', gulpSequence('pull-latest', ['app-build']));

function gitHubLogin(){
  //Fetches user input for github login
  var deffered = Q.defer();
  console.log("Github authentication");
  prompt.start();
  var user,
      pw;

  var schema = {
    properties: {
      user: {
        message: 'Your github username',
        required: true
      },
      password: {
        hidden: true
      }
    }
  };


  prompt.get(schema, function (err, result) {
    if(err){
      deffered.reject(err);
      return;
    }
    var output = {};
    output.user = result.user;
    output.pw = result.password;
    deffered.resolve(output);
  });

  return deffered.promise;
}
