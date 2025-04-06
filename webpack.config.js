const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');
const dotenv = require('dotenv');

// Load environment variables based on NODE_ENV
const env = process.env.NODE_ENV || 'development';
const envFile = env === 'production' ? '.env.production' : '.env.development';
const envPath = path.resolve(__dirname, `app/frontend/${envFile}`);
const envVars = dotenv.config({ path: envPath }).parsed || {};

// Create environment variables to inject
const envKeys = {
  'process.env': Object.keys(envVars).reduce((prev, key) => {
    prev[key] = JSON.stringify(envVars[key]);
    return prev;
  }, {
    'NODE_ENV': JSON.stringify(env)
  })
};

module.exports = {
  entry: './app/frontend/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
    publicPath: '/'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif|ico)$/,
        type: 'asset/resource',
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/,
        type: 'asset/resource',
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx']
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './app/frontend/index.html',
      filename: 'index.html'
    }),
    new webpack.DefinePlugin(envKeys)
  ],
  devServer: {
    static: [
      {
        directory: path.join(__dirname, 'dist'),
      },
      {
        directory: path.join(__dirname, 'public'),
      }
    ],
    port: 3009,
    proxy: {
      '/api': 'http://app:8009'
    },
    historyApiFallback: true,
    open: true,
    hot: true
  }
}; 