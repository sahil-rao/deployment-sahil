module.exports = function(dirname){
   return {
    entry: dirname+'src/main.js',
    output: {
        filename: 'bundle.js'
    },
    resolve: {
      root: '/home/ubuntu',
      modulesDirectories: [
        'node_modules',
        '.'
      ],
      fallback: ['/home/ubuntu/node_modules'],
    },
    resolveLoader: {
      root: '/home/ubuntu',
      modulesDirectories: [
        'node_modules',
        '.'
      ],
      fallback: ['/home/ubuntu/node_modules'],
    },
    module: {
      loaders: [
        { test: /\.less$/,
          loader: 'style-loader!css-loader!less-loader'
        },
        {
          test: /\.css$/,
          loader: 'style!css'
        },
        {
          test: /.jsx?$/,
          loader: 'babel-loader',
          exclude: /node_modules/,
          query: {
            presets: ['es2015', 'react']
          }
        }
      ]
    },
  };
};
