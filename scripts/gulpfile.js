var gulp = require('gulp'),
    gulpConfig = require('./gulp-config'),
    webpack = require('webpack-stream'),
    fs = require('fs-extra'),
    fsj = require('fs-jetpack'),
    tar = require('gulp-tar'),
    args = require('yargs').argv,
    Git = require("nodegit"),
    prompt = require("prompt"),
    Q = require('q'),
    shell = require('gulp-shell'),
    gulpSequence = require('gulp-sequence'), //Remove this once we upgrade to gulp 4.0
    eslint = require('gulp-eslint'),
    gulpIf = require('gulp-if'),
    gzip = require('gulp-gzip');

var branch = args.branch || 'master';
var xplainDir = args.xplainDir || null;
var fixEslint = args.fix || false;
var jshintSrc = [gulpConfig.uiDir+'xplain.io/**/*.js', gulpConfig.uiDir+'xplain.io/**/*.jsx', '!'+gulpConfig.uiDir+'xplain.io/public/js/libs/**/*.js',
'!'+gulpConfig.uiDir+'xplain.io/node_modules/**/*.js', '!'+gulpConfig.uiDir+'xplain.io/app/libraries/**/*.js','!'+gulpConfig.uiDir+'xplain.io/public/build/**/*.js', '!'+gulpConfig.uiDir+'xplain.io/test/**/*.js'];

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

gulp.task('webpack-build', function(){
  console.log("Compiling code");
  var dir = xplainDir || gulpConfig.uiDir+'xplain.io/';
  fs.copySync(dir+'src/index.html', dir+'public/build/index.html');
  return gulp.src(dir+'src/main.js')
    .pipe(webpack(require(dir+'src/webpack.config.js')))
    .pipe(gulp.dest(dir+'public/build/'));
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
      overwrite: true,
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

gulp.task('vm-setup', function(){
  return fsj.copy('/home/xplain/', '/etc/init/', {matching:'*.cfg'})
  .then(fsj.dir('~/tmp', {empty:true}))
  .then(fsj.move(gulpConfig.vmDest+'node_modules', '~/tmp/'))
  .then(fsj.copy(gulpConfig.uiDir+'xplain.io/', gulpConfig.vmDest, {
    overwrite:true,
    matching: ['!node_modules/**']
  }))
  .then(fsj.move('~/tmp/node_modules', gulpConfig.vmDest))
  .catch(function(err){
    console.error(err);
  });
});

gulp.task("eslint", function(){
  var config = {
		configFile: gulpConfig.uiDir+'.eslintrc.json',
    fix: fixEslint
  };
  return gulp.src(jshintSrc)
		.pipe(eslint(config))
		.pipe(eslint.format())
    .pipe(gulpIf(isFixed, gulp.dest(gulpConfig.uiDir+'xplain.io')));
});

gulp.task('vm-install-npm', shell.task(['npm install'], {verbose:true, cwd:gulpConfig.vmDest}));

gulp.task("push-app-aws", shell.task([
  's3cmd sync '+gulpConfig.uiDir+'xplain.io.tar.gz s3://'+gulpConfig.s3Bucket+'/'
]));
gulp.task("push-admin-aws", shell.task([
  's3cmd sync '+gulpConfig.uiDir+'optimizer_admin.tar.gz s3://'+gulpConfig.s3Bucket+'/'
]));
gulp.task("push-api-aws", shell.task([
  's3cmd sync '+gulpConfig.uiDir+'optimizer_api.tar.gz s3://'+gulpConfig.s3Bucket+'/'
]));

//gulp.task('full-build', gulpSequence('pull-latest', ['app-build', 'test-build', 'api-build', 'admin-build']));
gulp.task('full-build', gulpSequence('pull-latest', 'app-build'));
gulp.task('full-deploy', gulpSequence('full-build', 'push-app-aws'));

gulp.task('update-vm', gulpSequence('pull-latest', 'vm-setup', 'vm-install-npm'));

function gitHubLogin(){
  //Fetches user input for github login
  var deffered = Q.defer();
  var output = {};
  console.log("Github authentication");

  if(args.gitUser){
    console.log("Github username found in args");
    output.user = args.gitUser;
  }
  if(args.gitPw){
    console.log("Github password found in args");
    output.pw = args.gitPw;
  }
  if(gulpConfig.gitUser){
    console.log("Github username found in config");
    output.user = gulpConfig.gitUser;
  }
  if(gulpConfig.gitPw){
    console.log("Github password found in config");
    output.pw = args.gitPw;
  }
  if(output.pw && output.user){
    deffered.resolve(output);
    return deffered.promise;
  }

  prompt.start();

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

    output.user =  result.user;
    output.pw =  result.password;
    deffered.resolve(output);
  });

  return deffered.promise;
}


function isFixed(file) {
    // Has ESLint fixed the file contents
    return file.eslint != null && file.eslint.fixed;
}
