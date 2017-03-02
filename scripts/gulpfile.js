/*
Documentation: https://docs.google.com/document/d/1B7CK9edy6CJsHWzQqEV7xupZeFUvy6I7pzJN6Qk99rQ/edit?usp=sharing
*/

var gulp = require('gulp'),
    guppy = require('git-guppy')(gulp)
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
    gzip = require('gulp-gzip'),
    gitCred = require('git-credential-node');

var branch = args.branch || 'master';
var xplainDir = args.xplainDir || null;
var fixEslint = args.fix || false;


if(!gulpConfig.workDir) throw (new Error("No working directory found in gulp-config. Ensure that workDir is declared."));

var dirs = {
  ui : gulpConfig.dockerUI || gulpConfig.workDir+'/UI',
  outputDir: gulpConfig.outputDir,
  vm: gulpConfig.vmDir
}

var jshintSrc = [dirs.ui+'xplain.io/**/*.js', dirs.ui+'xplain.io/**/*.jsx', '!'+dirs.ui+'xplain.io/public/js/libs/**/*.js',
'!'+dirs.ui+'xplain.io/node_modules/**/*.js', '!'+dirs.ui+'xplain.io/app/libraries/**/*.js','!'+dirs.ui+'xplain.io/public/build/**/*.js', '!'+dirs.ui+'xplain.io/test/**/*.js',
'!'+dirs.ui+'xplain.io/src/cloudera-ui/**/*.js'];



gulp.task('ensure-working-dir', function(){
  console.log("Ensuring working directory exists.")
  return ensureDir(gulpConfig.workDir);
});
gulp.task('ensure-output-dir', function(){
  console.log("Ensuring output directory exists.")
  return ensureDir(gulpConfig.outputDir);
});

gulp.task('purge-ui', function(){
  console.log("Cleaning UI directory");
  var deferred = Q.defer();
  fs.emptyDir(dirs.ui, function(err){
    if(err){
      throw err;
    }
    deferred.resolve();
  });

  return deferred.promise;
});

gulp.task('pull-app', ['purge-ui'], function(){
  console.log("Pulling latest UI code");
  return pullFromGithub(gulpConfig.gitUrls.ui, dirs.ui, 'ui');
});

gulp.task('webpack-build', function(){
  console.log("Compiling code");
  var dir = xplainDir || dirs.ui+'/xplain.io/';
  return webpack(require(dir+'src/webpack.config.js'))
    .pipe(gulp.dest(dir+'public/build/'));
});

/*
Build main application
*/
gulp.task('app-build', ["webpack-build"], function(){
  var dir = dirs.ui;
  if(dirs.vm){
    console.log("VM Detected");
  }
  try{
    var dest = fsj.dir(dir+'/tmp/xplain.io/xplain.io', {empty:true});
    fsj.copy(dir+'/xplain.io', dest.path(), {
      overwrite: true,
      matching: ['!node_modules/**']
    });
    fs.removeSync(dir+'/tmp/xplain.io/xplain.io/node_modules');
    fs.removeSync(dirs.outputDir+'xplain.io.tar.gz');
    return gulp.src(dir+'/tmp/xplain.io/**')
        .pipe(tar('xplain.io.tar'))
        .pipe(gzip())
        .pipe(gulp.dest(dirs.outputDir))
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

gulp.task('quick-vm-update', ['webpack-build'], function(){
  return fsj.dirAsync(dirs.vm+'public', {empty:true})
  .then(fsj.dirAsync(dirs.vm+'views', {empty:true}))
  .then(fsj.dirAsync(dirs.vm+'app', {empty:true}))
  .then(fsj.copyAsync(dirs.ui+'/xplain.io/public', dirs.vm+'public', {overwrite:true}))
  .then(fsj.copyAsync(dirs.ui+'/xplain.io/app', dirs.vm+'app', {overwrite:true}))
  .then(fsj.copyAsync(dirs.ui+'/xplain.io/views', dirs.vm+'views', {overwrite:true}))
  .catch(function(err){
    console.error(err);
  });
});

//Not working yet
gulp.task('vm-setup', function(){
  return fsj.copyAsync('/home/xplain/', '/etc/init/', {matching:'*.cfg', overwrite:true})
  .then(fsj.dirAsync(dirs.ui+'/tmp', {empty:true}))/*
  .then(fsj.moveAsync(gulpConfig.vmDir+'node_modules', dirs.ui+'/tmp/'))
  .then(fsj.copyAsync(dirs.ui+'/xplain.io/', gulpConfig.vmDir, {
    overwrite:true,
    matching: ['!node_modules/**']
  }))
  .then(fsj.moveAsync(dirs.ui+'/tmp/node_modules', gulpConfig.vmDir))
  */
  .catch(function(err){
    console.error(err);
  });
});

gulp.task("eslint", function(){
  var config = {
		configFile: dirs.ui+'/xplain.io/.eslintrc.json',
    fix: fixEslint
  };
  return gulp.src(jshintSrc)
		.pipe(eslint(config))
		.pipe(eslint.format())
    .pipe(gulpIf(isFixed, gulp.dest(dirs.ui+'xplain.io')));
});

gulp.task('vm-install-npm', shell.task(['sudo npm install'], {verbose:true, cwd:gulpConfig.vmDir}));

gulp.task("push-app-aws", shell.task([
  's3cmd sync '+dirs.ui+'xplain.io.tar.gz s3://'+gulpConfig.s3Bucket+'/'
]));
gulp.task("push-admin-aws", shell.task([
  's3cmd sync '+dirs.ui+'optimizer_admin.tar.gz s3://'+gulpConfig.s3Bucket+'/'
]));
gulp.task("push-api-aws", shell.task([
  's3cmd sync '+dirs.ui+'optimizer_api.tar.gz s3://'+gulpConfig.s3Bucket+'/'
]));

//gulp.task('full-build', gulpSequence('pull-latest', ['app-build', 'test-build', 'api-build', 'admin-build']));
gulp.task('full-build', gulpSequence('pull-app', 'app-build'));
gulp.task('full-deploy', gulpSequence('full-build', 'push-app-aws'));

gulp.task('update-vm', gulpSequence('pull-app', 'vm-setup', 'vm-install-npm'));

function gitHubLogin(repo){
  //Fetches user input for github login
  var deffered = Q.defer();
  var output = {};

  console.log("Github authentication");
  if(gulpConfig.gitLogins){
    output.user = gulpConfig.gitLogins[repo].user || gulpConfig.gitLogins.default.user;
    output.pw = gulpConfig.gitLogins[repo].pw || gulpConfig.gitLogins.default.pw;
    if(output.user){
      console.log("Github username found in config");
    }
    if(output.pw){
      console.log("Github password found in config");
    }
  }

  //Arguments will override the authentication for all tasks.
  if(args.gitUser){
    console.log("Github username found in args");
    output.user = args.gitUser;
  }
  if(args.gitPw){
    console.log("Github password found in args");
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
        message: 'Your '+ repo +' github credentials',
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

    output.user = result.user;
    output.pw = result.password;
    deffered.resolve(output);
  });

  return deffered.promise;
}

function pullFromGithub(gitURL, dir, repo){
  var defered = Q.defer();
  gitCred.fill(gitURL, function (err, data) {
    // data will contain any stored credentials, or will be {}
    if(err){
      console.log(err);
    }
    if(!data){
      gitHubLogin(repo).then(function(out){
        var d = {
          username:out.user,
          password:out.pw,
          url:gitURL
        }
        gitCred.approveSync(d);
        gitClone(d, gitURL, dir)
        .then(function(d){defered.resolve(d)})
        .catch(function(e){defer.reject(e)});
      })
    }
    else{
      gitClone(data, gitURL, dir)
      .then(function(d){defered.resolve(d)})
      .catch(function(e){defer.reject(e)});
    }
  });
  return defered.promise;
}

function gitClone(creds, gitURL, dir){
  var defered = Q.defer();
  var opts = {
    checkoutBranch: branch,
    fetchOpts: {
      callbacks: {
        credentials: function() { return Git.Cred.userpassPlaintextNew(creds.username, creds.password)}
      }
    }
  };
  console.log("Credentials acquired. Cloning.")
  Git.Clone(gitURL, dir, opts)//Git Clone returns a promise
  .then(function(d){
    defered.resolve(d);
  })
  .catch(function(err) {
    console.log(err);
    defered.reject(err);
  });
  return defered.promise;
}

function isFixed(file) {
    // Has ESLint fixed the file contents
    return file.eslint != null && file.eslint.fixed;
}

function ensureDir(dir){
  var def = Q.defer();
  fs.ensureDir(dir, function (err) {
    if(err){
      console.log(err);
      def.reject(err);
      return;
    }
    def.resolve();
  });
  return def.promise;
}
